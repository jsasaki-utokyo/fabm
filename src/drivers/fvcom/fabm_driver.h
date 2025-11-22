! FVCOM driver for FABM
! 3D unstructured grid: (horizontal_nodes, vertical_levels)
!
! Configuration optimized for ERSEM coupling with surface/bottom state support
! Updated: 2025-10-23 for FVCOM-FABM-ERSEM integration

! 2D arrays: (horizontal_nodes, vertical_levels)
#define _FABM_DIMENSION_COUNT_ 2
#define _FABM_DEPTH_DIMENSION_INDEX_ 2
#define _FABM_VECTORIZED_DIMENSION_INDEX_ 1
#define _FABM_HORIZONTAL_DIMENSION_INDEX_ 1

! Variable bottom depth per horizontal node (unstructured grid)
#define _FABM_BOTTOM_INDEX_ -1

! Vertical indexing: bottom to surface (matches FVCOM convention)
#define _FABM_VERTICAL_BOTTOM_TO_SURFACE_

! Use contiguous arrays for performance
#define _FABM_CONTIGUOUS_

! Masking configuration for wet/dry elements
#define _FABM_MASK_TYPE_ integer
#define _FABM_UNMASKED_VALUE_ 1
#define _FABM_HORIZONTAL_MASK_

! Include FABM preprocessor definitions
! This MUST be done after host-specific variables are defined (above)
#include "fabm.h"
