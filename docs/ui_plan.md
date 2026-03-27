# DorkVault UI Plan

This document describes the intended shape of the DorkVault desktop interface and how the current implementation maps to that plan.

## UI Goals

- simple and professional desktop interface
- fast access to large technique catalogs
- minimal visual noise
- clear selection and detail workflow
- scalable layout that still feels lightweight

## Primary Layout

The current design is built around a horizontal splitter with four working regions:

1. left sidebar
   Navigation and category access.
2. top bar
   Target input, search, quick filtering, and primary actions.
3. center list
   Technique browsing in list or compact card mode.
4. right detail panel
   Technique details, variables, template, preview, and actions.

A status bar sits at the bottom for lightweight feedback.

## Main Window Sections

### Sidebar

Navigation items:

- All Techniques
- Favorites
- Recent
- Categories
- Settings
- About

Responsibilities:

- switch high-level dataset views
- expose category filtering
- stay visually quiet and reusable

### Top Bar

Responsibilities:

- target input for values such as domain, company, or keyword
- text search across the loaded catalog
- category quick filter
- common actions such as copy, launch, favorite, export, and new custom technique

Keyboard shortcuts already supported:

- `Ctrl+F` focus search
- `Ctrl+L` focus target input
- `Ctrl+C` copy query when appropriate
- `Ctrl+O` open in browser when appropriate
- `Ctrl+E` export

### Technique List

Responsibilities:

- display techniques from the current filtered result set
- support single selection
- show result count
- support list and card presentation
- stay responsive with larger catalogs

Implementation note:

The list uses a model/delegate approach instead of rebuilding many child widgets, which is the right direction for larger datasets.

### Detail Panel

Responsibilities:

- show the selected technique clearly
- render a useful preview from the current target input
- expose copy, launch, and favorite actions
- expose edit/delete only for user-created custom techniques

It should remain information-dense without becoming cluttered.

## Visual Direction

The current theme direction is:

- matte black and dark gray surfaces
- white foreground text
- one subtle accent color
- soft borders and restrained hover states
- clear selected states without “hacker UI” styling

## Current Status

Implemented today:

- splitter-based shell
- reusable sidebar
- reusable top bar
- scalable technique list with result count and empty state
- detail panel with live preview
- status bar feedback
- light QSS theme

Not implemented yet or intentionally lightweight:

- About content
- richer multi-variable input workflows
- screenshot assets for documentation
- optional secondary views such as advanced filters or pack management

## Next UI Iteration Ideas

- add a compact variable editor for techniques that need more than one input
- add a lightweight “pack/source” indicator in the detail panel
- add an about page with version, paths, and log-file location
- add optional toolbar layout persistence
- refine export flow into a dedicated dialog if it grows more complex

## UI Constraints To Preserve

- do not hardcode large button grids for techniques
- do not overload the interface with decorative styling
- do not let main window logic drift into widget internals unnecessarily
- prefer reusable widgets and service-backed behavior
