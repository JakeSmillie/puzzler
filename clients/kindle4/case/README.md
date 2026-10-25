# Kindle 4 case

No case designed yet.

## Layout

```
src/        editable CAD source (OpenSCAD .scad, FreeCAD .FCStd, Fusion .f3d, ...)
README.md   this file: parts, print settings, assembly
```

Keep the editable source in git. Exported STL/3MF files are large binaries, so
don't commit them. Attach them to a GitHub Release instead, or track them with
Git LFS (`git lfs track "*.stl" "*.3mf"`).

## Kindle 4 dimensions

Measure your own device before printing, as these are nominal values.

- Body: 166 × 114 × 8.7 mm
- Screen: 6", 600×800, about 122 × 91 mm visible
- Buttons to leave access to:
  - page forward and back on both long edges;
  - 5-way, Back, Keyboard, Menu and Home below the screen;
  - power and micro-USB on the bottom edge.
