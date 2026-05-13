# Conversion Rules

Support these length units:

- `m`: meter, base factor 1.0
- `km`: kilometer, base factor 1000.0
- `cm`: centimeter, base factor 0.01
- `mm`: millimeter, base factor 0.001
- `ft`: foot, base factor 0.3048

The conversion formula is:

```text
value_in_meters = input_value * source_factor
converted_value = value_in_meters / target_factor
```

Invalid units should cause a non-zero exit and a clear error message.
