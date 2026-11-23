"""Structures section (M3): the facility registry the planner
multiplies against.

One page renders the registry grouped by activity, the sync-import
card, the multiplier reference, and the add/edit form (the mockup's
single-form design: the form is always "this structure's registration
for the selected activity" — creating a structure, editing a
registration, and registering a further activity on an existing
structure are the same form in different states). Saves are
server-rendered form posts with redirects; the system type-ahead is
the one JSON endpoint. Page renders stay DB-pure — ESI (the system
lookup) happens at save time only, through the cached public client.
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy import select

from ..deps import DbDep, EsiDep, is_authenticated
from ..facilities import (
    ACTIVITIES,
    ACTIVITY_LABELS,
    ACTIVITY_RIG_FIELDS,
    ACTIVITY_STRUCTURE_TYPES,
    ENGINEERING_COMPLEXES,
    RIG_TIERS,
    STRUCTURE_TYPES,
    import_candidates,
    registration_rows,
    resolve_system,
    system_suggestions,
)
from ..models import Structure, StructureRegistration, UniverseLocation
from ..templates import templates

router = APIRouter()

# The multiplier reference card: static rows from the facilities data
# (values pinned with provenance in app/facilities.py).
_MULTIPLIER_ROWS = [
    (
        "Engineering-complex hull",
        "job time on jobs run in the structure",
        "Raitaru ×0.85 · Azbel ×0.80 · Sotiyo ×0.70 · material ×0.99 all · "
        "job cost ×0.97/×0.96/×0.95",
    ),
    (
        "Refinery hull",
        "reaction time",
        "Tatara ×0.75 · Athanor no reaction-time bonus",
    ),
    (
        "ME rig × security",
        "material consumption (manufacturing, reactions)",
        "T1 2.0% / T2 2.4% base · EC rigs ×1.0 high / ×1.9 low / ×2.1 null · "
        "reactor rigs ×1.0 low / ×1.1 null (reactions are low/null only)",
    ),
    (
        "TE rig × security",
        "job time (manufacturing, reactions, invention)",
        "T1 20% / T2 24% base, the same per-family security scaling",
    ),
    (
        "Tax + cost index",
        "install cost",
        "base × (1 + tax) × system cost index — indices sync at M15",
    ),
]


def _login() -> RedirectResponse:
    return RedirectResponse("/", status_code=302)


def _tax_fraction(raw: str) -> float | None:
    """'0.5' or '0.5%' (percent) → 0.005; empty → None (NPC-set)."""
    raw = (raw or "").strip().rstrip("%").strip()
    if not raw:
        return None
    value = float(raw) / 100.0
    if not 0.0 <= value <= 1.0:
        raise ValueError("tax out of range")
    return value


async def _form_structure(
    db: DbDep, structure_id: int | None
) -> Structure | None:
    if structure_id is None:
        return None
    return (
        await db.execute(select(Structure).where(Structure.id == structure_id))
    ).scalar_one_or_none()


@router.get("/structures")
async def structures_page(
    request: Request,
    db: DbDep,
    esi: EsiDep,
    structure: int | None = None,
    activity: str | None = None,
):
    """The registry page. The import prefill resolves the sighting's
    system security through the cached ESI client — an action-triggered
    render (the Import chip was just clicked), like the roster's
    metadata fetches, not a passive page load."""
    if not is_authenticated(request):
        return _login()
    # The import card links with ?import=<location id> ("import" is a
    # reserved word, so it can't be a parameter name).
    import_raw = request.query_params.get("import", "")
    import_location = int(import_raw) if import_raw.isdigit() else None

    rows = await registration_rows(db)
    # Per-structure registered activities: the registry rows cross-link
    # a structure's other registrations and offer "+ activity".
    structure_activities: dict[int, list[str]] = {}
    for row in rows:
        structure_activities.setdefault(row.structure_id, []).append(row.activity)
    groups = [
        (activity_key, ACTIVITY_LABELS[activity_key],
         [row for row in rows if row.activity == activity_key])
        for activity_key in ACTIVITIES
    ]

    # The form's edit state: (structure, activity) selects a
    # registration to edit, or an unregistered activity on an existing
    # structure (the add-registration mode — `?structure=<id>&form=add`,
    # the registry rows' "+ activity" control). An import location
    # pre-fills a blank form from a sync sighting. The panel itself is
    # hidden unless one of these states (or ?form=add) asks for it —
    # the Add structure button and the row Edit links reveal it.
    form_structure = await _form_structure(db, structure)
    form_registration = None
    if form_structure is not None and activity in ACTIVITIES:
        form_registration = (
            await db.execute(
                select(StructureRegistration).where(
                    StructureRegistration.structure_id == form_structure.id,
                    StructureRegistration.activity == activity,
                )
            )
        ).scalar_one_or_none()
    # The structure's registered activities — for the form's chip
    # markers (a picked registered activity edits; an unregistered one
    # registers) and the registry rows' cross-links.
    registered: list[str] = []
    if form_structure is not None:
        registered = list(
            (
                await db.execute(
                    select(StructureRegistration.activity)
                    .where(StructureRegistration.structure_id == form_structure.id)
                    .order_by(StructureRegistration.id)
                )
            ).scalars()
        )
    if activity not in ACTIVITIES:
        if form_structure is not None:
            # The add-registration mode starts on the first activity
            # the structure does not host yet; fully registered falls
            # back to its first registration (plain edit).
            activity = next(
                (a for a in ACTIVITIES if a not in registered),
                registered[0] if registered else "manufacturing",
            )
        else:
            activity = "manufacturing"
        if form_structure is not None and activity in registered:
            form_registration = (
                await db.execute(
                    select(StructureRegistration).where(
                        StructureRegistration.structure_id == form_structure.id,
                        StructureRegistration.activity == activity,
                    )
                )
            ).scalar_one_or_none()
    imported = None
    imported_system_name = None
    if import_location is not None and form_structure is None:
        imported = (
            await db.execute(
                select(UniverseLocation).where(
                    UniverseLocation.location_id == import_location
                )
            )
        ).scalar_one_or_none()
        if imported is not None and imported.system_id is not None:
            imported_system_name = (
                await db.execute(
                    select(UniverseLocation.name).where(
                        UniverseLocation.location_id == imported.system_id,
                        UniverseLocation.kind == "solar_system",
                    )
                )
            ).scalar_one_or_none()
    # The type-ahead input's display value: never a bare None.
    form_system_name = (
        (form_structure.system_name if form_structure else None)
        or imported_system_name
        or ""
    )
    # The security chips' initial selection: the structure's stored class
    # in edit mode; the imported sighting's system resolves through ESI
    # (its class is what the save would store); none on a blank form.
    form_security_class = form_structure.security_class if form_structure else None
    if form_structure is None and imported is not None and imported.system_id:
        resolved_import = await resolve_system(db, esi, imported.system_id)
        if resolved_import is not None:
            form_security_class = resolved_import[1]

    return templates.TemplateResponse(
        request,
        "structures.html",
        {
            "authenticated": True,
            "active": "structures",
            "groups": groups,
            "counts": {
                "registrations": len(rows),
                "structures": len({row.structure_id for row in rows}),
            },
            "import_candidates": await import_candidates(db),
            "multiplier_rows": _MULTIPLIER_ROWS,
            # The panel shows only when a link asked for it: the Add
            # structure button (?form=add), an Edit link (structure +
            # activity), or an import.
            "show_form": (
                request.query_params.get("form") == "add"
                or form_structure is not None
                or imported is not None
            ),
            # Form state
            "form_structure": form_structure,
            "form_activity": activity if activity in ACTIVITIES else None,
            "form_registration": form_registration,
            "registered_activities": registered,
            "structure_activities": structure_activities,
            "imported": imported,
            "form_system_name": form_system_name,
            "form_security_class": form_security_class,
            "structure_types": STRUCTURE_TYPES,
            "activity_types": ACTIVITY_STRUCTURE_TYPES,
            "rig_tiers": RIG_TIERS,
            "activities": ACTIVITIES,
            "activity_labels": ACTIVITY_LABELS,
            "rig_fields": ACTIVITY_RIG_FIELDS,
        },
    )


@router.get("/structures/systems/search")
async def structures_systems_search(
    request: Request, db: DbDep, esi: EsiDep, q: str = ""
):
    if not is_authenticated(request):
        return JSONResponse({"systems": []}, status_code=403)
    return JSONResponse({"systems": await system_suggestions(db, esi, q)})


@router.post("/structures")
async def structures_save(request: Request, db: DbDep, esi: EsiDep):
    """Create-or-update: the structure (creating it when the form carries
    no structure id) and its registration for the selected activity —
    one form, three states (new structure, edit registration, register
    a further activity)."""
    if not is_authenticated(request):
        return RedirectResponse("/", status_code=303)
    form = await request.form()

    errors: list[str] = []
    activity = form.get("activity", "")
    if activity not in ACTIVITIES:
        errors.append("Pick an activity.")
    name = (form.get("name", "") or "").strip()
    if not name:
        errors.append("A structure name is required.")
    structure_type = form.get("structure_type", "")
    if structure_type not in STRUCTURE_TYPES:
        errors.append("Pick a structure type.")
    elif activity in ACTIVITIES and structure_type not in ACTIVITY_STRUCTURE_TYPES[
        activity
    ]:
        errors.append(
            f"{STRUCTURE_TYPES[structure_type]} cannot host "
            f"{ACTIVITY_LABELS[activity].lower()} jobs."
        )
    me_rig = form.get("me_rig", "none")
    te_rig = form.get("te_rig", "none")
    if me_rig not in RIG_TIERS or te_rig not in RIG_TIERS:
        errors.append("Pick a rig tier.")
    tax_rate: float | None
    try:
        tax_rate = _tax_fraction(form.get("tax_rate", ""))
    except ValueError:
        errors.append("Tax rate must be a percentage between 0 and 100.")
        tax_rate = None

    # System: a selected id wins (ESI resolves name + security at save
    # time); without one, a hand-set class applies.
    system_id = (form.get("system_id", "") or "").strip()
    security_class = form.get("security_class", "") or None
    if security_class not in (None, "high", "low", "null"):
        errors.append("Pick a security class.")

    supercap = form.get("supercapital_assembly") == "on"
    is_default = form.get("is_default") == "on"
    location_id = (form.get("location_id", "") or "").strip()
    location_id = int(location_id) if location_id.isdigit() else None
    structure_id = (form.get("structure_id", "") or "").strip()
    structure_id = int(structure_id) if structure_id.isdigit() else None

    structure = await _form_structure(db, structure_id)
    if structure_id is not None and structure is None:
        errors.append("That structure no longer exists.")

    resolved: tuple[str | None, str | None] | None = None
    if system_id.isdigit():
        resolved = await resolve_system(db, esi, int(system_id))
        if resolved is None:
            errors.append("That system could not be resolved — pick one from the list.")

    # The capability is validated, not trusted: engineering complexes
    # in nullsec systems only (the pin — CCP docs say supercapital
    # construction needs sov + the Supercapital Construction Facilities
    # upgrade; the flag gates the final hull job). The security the
    # save will store: the selected system's class when one is picked
    # (the form round-trips system_id on edit, so it re-resolves),
    # otherwise the hand-set class.
    effective_security = resolved[1] if resolved is not None else security_class
    if supercap and not errors:
        if structure_type not in ENGINEERING_COMPLEXES:
            errors.append(
                "Supercapital assembly is an engineering-complex capability."
            )
        elif effective_security != "null":
            errors.append(
                "Supercapital assembly requires a nullsec system (unconfirmed "
                "pin — CCP docs point at sov + the Supercapital Construction "
                "Facilities upgrade)."
            )

    if errors:
        rows = await registration_rows(db)
        return templates.TemplateResponse(
            request,
            "structures.html",
            {
                "authenticated": True,
                "active": "structures",
                "groups": [
                    (key, ACTIVITY_LABELS[key],
                     [r for r in rows if r.activity == key])
                    for key in ACTIVITIES
                ],
                "counts": {
                    "registrations": len(rows),
                    "structures": len({r.structure_id for r in rows}),
                },
                "import_candidates": await import_candidates(db),
                "multiplier_rows": _MULTIPLIER_ROWS,
                "form_structure": structure,
                "show_form": True,  # errors render inside the panel
                "form_activity": activity if activity in ACTIVITIES else None,
                "form_registration": None,
                "imported": None,
                "structure_types": STRUCTURE_TYPES,
                "activity_types": ACTIVITY_STRUCTURE_TYPES,
                "rig_tiers": RIG_TIERS,
                "activities": ACTIVITIES,
                "activity_labels": ACTIVITY_LABELS,
                "rig_fields": ACTIVITY_RIG_FIELDS,
                "form_errors": errors,
                # Echo the submitted values back into the form.
                "form_values": {
                    "name": name,
                    "structure_type": structure_type,
                    "activity": activity,
                    "me_rig": me_rig,
                    "te_rig": te_rig,
                    "tax_rate": form.get("tax_rate", ""),
                    "system_id": system_id,
                    "supercapital_assembly": supercap,
                    "is_default": is_default,
                    "security_class": security_class or "",
                },
            },
            status_code=422,
        )

    # Structure create-or-update.
    if structure is None:
        structure = Structure(
            name=name,
            structure_type=structure_type,
            location_id=location_id,
        )
        db.add(structure)
        await db.flush()
    else:
        structure.name = name
        structure.structure_type = structure_type
        if location_id is not None:
            structure.location_id = location_id
    if resolved is not None:
        structure.system_id = int(system_id)
        structure.system_name = resolved[0]
        # ESI classifies; when it was unreachable and only the local
        # row named the system, the hand-set class applies.
        structure.security_class = resolved[1] or security_class
    elif not system_id.isdigit():
        structure.system_id = None
        structure.system_name = None
        structure.security_class = security_class
    structure.supercapital_assembly = supercap

    # Registration create-or-update for (structure, activity).
    registration = (
        await db.execute(
            select(StructureRegistration).where(
                StructureRegistration.structure_id == structure.id,
                StructureRegistration.activity == activity,
            )
        )
    ).scalar_one_or_none()
    if registration is None:
        registration = StructureRegistration(
            structure_id=structure.id, activity=activity
        )
        db.add(registration)
    registration.me_rig = me_rig
    registration.te_rig = te_rig
    registration.tax_rate = tax_rate

    # Default demotion: unchecking leaves the activity default-less;
    # setting a new default demotes the previous one. The demotion MUST
    # reach the database before the promotion flushes — SQLAlchemy
    # batches same-table updates into one executemany ordered by
    # primary key, so code order means nothing: a promotion landing
    # first momentarily creates two defaults and trips the partial
    # unique index (the crash a promote-with-lower-id edit hit). The
    # flush between them is the barrier.
    registration.is_default = False
    if is_default:
        others = (
            await db.execute(
                select(StructureRegistration).where(
                    StructureRegistration.activity == activity,
                    StructureRegistration.id != registration.id,
                    StructureRegistration.is_default,
                )
            )
        ).scalars().all()
        for other in others:
            other.is_default = False
        await db.flush()
        registration.is_default = True

    await db.commit()
    return RedirectResponse("/structures", status_code=303)


@router.post("/structures/{structure_id}/delete")
async def structures_delete(request: Request, db: DbDep, structure_id: int):
    """Delete a structure and its registrations (cascade)."""
    if not is_authenticated(request):
        return RedirectResponse("/", status_code=303)
    structure = (
        await db.execute(select(Structure).where(Structure.id == structure_id))
    ).scalar_one_or_none()
    if structure is not None:
        await db.delete(structure)
        await db.commit()
    return RedirectResponse("/structures", status_code=303)


@router.post("/structures/{structure_id}/{registration_id}/delete")
async def structures_registration_delete(
    request: Request, db: DbDep, structure_id: int, registration_id: int
):
    """Delete one registration; the structure stays for its other
    activities (and is removed with its last registration — a structure
    registered for nothing is not a facility)."""
    if not is_authenticated(request):
        return RedirectResponse("/", status_code=303)
    registration = (
        await db.execute(
            select(StructureRegistration).where(
                StructureRegistration.id == registration_id,
                StructureRegistration.structure_id == structure_id,
            )
        )
    ).scalar_one_or_none()
    if registration is not None:
        await db.delete(registration)
        await db.flush()
        remaining = (
            await db.execute(
                select(StructureRegistration).where(
                    StructureRegistration.structure_id == structure_id
                )
            )
        ).scalars().all()
        if not remaining:
            structure = (
                await db.execute(
                    select(Structure).where(Structure.id == structure_id)
                )
            ).scalar_one_or_none()
            if structure is not None:
                await db.delete(structure)
        await db.commit()
    return RedirectResponse("/structures", status_code=303)
