# Original mockup prompt — verbatim

The prompt that produced these mockups, preserved exactly as written
(2026-11-17). Archived source material, not living guidance:
`ITERATION.md` is the working document — read this only if a question
comes up about what the original spec actually said.

> I want to mock up some potential interfaces for the build planner based
> on the current milestone targets leading up to the fork. We won't include
> things like market data etc. I want to primarily mock up what the reverse
> build stages would look like, along with the blueprint copy planner and
> job distribution planner. The way I'd expect this to work would be to
> open the build planner, which provides you a page with a search box that
> lets you find a particular blueprint (with auto-complete that shows all
> matching blueprints as you type, including the icon beside the matching
> blueprints).
>
> Once the blueprint is selected, an overview of the components and
> materials, along with their required counts, would be displayed. If the
> admin adjusts the target count, then the overview would update to match.
> A button within the build planner is provided to "Match From Inventory"
> so that only available blueprints in the inventory are shown. Showing
> multiple of the same blueprint would be possible, as an overlay including
> the location, ME, and TE values of the BPO or BPC would be displayed.
>
> At the bottom would be a "Calculate" button, which is what would execute
> the build plan calculations, resulting in the build plan with all data
> provided, including raw material requirements, blueprint copy
> requirements (number of BPCs and their run counts), and the job
> allocation overview. Additionally a visual indicator of the reverse
> product chain would be displayed. The available inventory from the
> hangar would be monitored, showing when materials are available that
> satisfy the various build stages. For raw materials, a list of materials,
> their target count and available count could be displayed, along with the
> percentage of materials towards the requirements (for example, if 5.3M
> tritanium is required and we have half of that, the percentage along with
> a thin horizontal bar would display 50% of materials available).
>
> Also on the page should be the job allocation display and guide.
> Alternatives can be suggested, but a starting point may be the characters
> and their job slots being show with whatever the job allocated to that
> slot should be, which would include the blueprint to use as part of the
> job, which could be of type reaction, copy, invention, or manufacture.
> The structure to run the job would also be on the indicator, along with
> the number of runs to execute the job for. If a job is in progress, then
> the screen would change slightly to indicate the target job is in
> progress, and its current status along with time-to-delivery. This would
> be shown for all available job slots based on the current available
> materials/components/reactions. Also a "next up" would be interesting to
> add, which would show the next job that should be executed in this slot
> once delivery is completed.
>
> I've described 2 separate pages: the build planner itself, and then the
> resulting build plan with all information calculated.
>
> Also on the build plan, it would display the blueprints you have that can
> satisfy the product chain. List all required blueprints, and an indicator
> whether the blueprint is in the inventory (Missing or Owned chip).
>
> The product chain one displayed would also be modifiable live. The build
> planner could identify build stages that they want to mark as "purchase"
> by selecting a "Purchase" chip. If selected the chip would turn into
> "Build" allowing the planner to switch between states. In either state,
> the stage would display the current state, such as "Missing inputs" when
> materials or components are not yet available, "Ready to build" when
> inputs are available and a job slot is free including when the blueprint
> copy/original is available, "Ready to Deliver" when the jobs that satisfy
> the stage are completed and ready to deliver, and "Stage Complete" once
> all outputs are delivered from the plan stage.
>
> I will likely want to iterate on this quite a bit. Any recommendations on
> how to mock this up? Doesn't need to be an interactive prototype right
> now, a static wireframe would be valuable.
>
> Consider the MILESTONES and TYPHOON-CHAIN files for appropriate context.
