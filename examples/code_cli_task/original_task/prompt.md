Using only the provided materials, build a small Python command-line tool for unit conversion.

Create the deliverable under `./outputs/unit_converter/`. The package must run with:

```bash
python -m unit_converter --value 3.5 --from km --to m --json
```

The JSON output for that command should include:

- `input_value`: 3.5
- `from_unit`: `"km"`
- `to_unit`: `"m"`
- `converted_value`: 3500.0

Support the units and conversion rules described in `./inputs/materials/conversion_rules.md`. Use only the Python standard library. Include a README and a small test file under the deliverable directory.
