# Changelog

## Unreleased

- Order XML accepts an optional `<finish>` element. `none` leaves the MakePlayingCards print type on full colour, `holographic` selects `EF_055` (`Holographic (front)`), and `shards` selects `EF_580` (`Holographic silver foil shards (front)`). Other `EF_` codes are passed through to the same dropdown. `<foil>true</foil>` and `<foil>false</foil>` are unchanged when `<finish>` is omitted. A present `<finish>` overrides `<foil>`. Orders with different finishes are not combined. `--no-combine-orders` still keeps every file separate.
