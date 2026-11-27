# MPC Autofill Desktop Tool

Our docs are available in the repo's [Wiki](https://github.com/chilli-axe/mpc-autofill/wiki/Desktop-Tool).

## Print type (`<finish>`)

`<details>` still accepts `<foil>true</foil>` and `<foil>false</foil>`. `true` selects MakePlayingCards' holographic front option. `false` leaves the print-type dropdown on the site default, full colour.

An optional `<finish>` element selects the print type directly. When it is present and not blank, it overrides `<foil>`. When it is omitted, `<foil>` behaves as before.

| `<finish>` | Print type | `dro_product_effect` value |
| --- | --- | --- |
| `none` | Full color print | dropdown left as-is |
| `holographic` | Holographic (front) | `EF_055` |
| `shards` | Holographic silver foil shards (front) | `EF_580` |
| an `EF_…` code | that MPC option | the same code |

`EF_055` and `EF_580` are the option values `publish.js` `renderEffectInfo()` loads into `dro_product_effect` from `https://www.makeplayingcards.com/api/publish/getproducteffectinfo.ashx`. Queried 2026-11-27 for [Custom Game Cards, 63×88mm](https://www.makeplayingcards.com/design/custom-blank-card.html) (product `PC140626-01`, hidden unit id `C380050185D1C1AF`) with `(S30) Standard Smooth` (`dro_paper_type` value `PA_014`) at the 18, 36, 55, and 612 card brackets. The same two codes came back for S27, S33, and M31. The response labels are `Holographic (front)` (`EF_055`, effect group `HOLOGRAPHIC`) and `Holographic silver foil shards (front)` (`EF_580`, effect group `HGCSHARD`). Other codes from that response can be passed through, for example `EF_581` (`Holographic gold foil shards (front)`). `(P10) Plastic` returned no print types, so a foil finish on P10 is rejected, as `<foil>true</foil>` already was.

Orders combine only when the card stock and the finish match. `<foil>true</foil>` and `<finish>holographic</finish>` are the same finish. `shards` does not combine with holographic. `--no-combine-orders` leaves every XML as its own project even when the finish matches. `<backs>` and `<cardback>` are unchanged: listed back slots keep their images, and `<cardback>` fills the slots `<backs>` did not cover.

```xml
<details>
    <quantity>36</quantity>
    <stock>(S30) Standard Smooth</stock>
    <foil>false</foil>
    <finish>shards</finish>
</details>
```

Sites other than MakePlayingCards do not support foil. A foil finish there produces the same warning as `<foil>true</foil>`, and the project is filled as non-foil.

The tool still only saves a Saved Project. It does not add the project to the cart.

## Build the Linux binary

The release workflow compiles `desktop-tool/autofill.py` with Nuitka as a onefile binary and names the Linux artifact `autofill-linux.bin`. From this repo, with Python 3.13:

```bash
cd desktop-tool
python3.13 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
# Nuitka packages this file. Use a Drive service-account JSON, or {} if you
# only upload local files.
echo '{}' > client_secrets.json
python -m nuitka autofill.py
```

Nuitka writes `autofill.bin` next to `autofill.py`. Rename it to `autofill-linux.bin` if you want the same filename as the GitHub release. The command is slow. `python autofill.py --help` runs the tool without compiling it.
