# Common parenting-time schedules, explained

A rotation is a pattern of days that repeats. Most shared schedules repeat every 14 days, so the pattern becomes clear once you lay out two weeks. Below, **A** and **B** are the two parents and each letter is one day (one overnight), starting on the rotation's start date.

All of these are built into the tool as presets. Run `custody-schedule presets` to list them.

## What is a 2-2-3 schedule?

Two days with one parent, two with the other, then three with the first. The following week the order flips, so each parent ends up with alternating long weekends.

```
Week 1:  A A B B A A A
Week 2:  B B A A B B B
```

Each parent has 7 of every 14 days. No one goes more than three days without the child, which makes 2-2-3 common for younger children. The cost is frequent handoffs: six exchanges every two weeks.

## What is a 2-2-5-5 schedule?

Two days, two days, then five and five. Each parent keeps the same weekdays every week (for example, A always has Monday and Tuesday), and the weekends alternate inside the five-day blocks.

```
Week 1:  A A B B A A A
Week 2:  A A B B B B B
```

Each parent has 7 of every 14 days, with four exchanges per cycle. Fixed weekdays make school-night routines and activities easier to plan.

## What is a 3-4-4-3 schedule?

Three days with one parent, four with the other; the next week the split reverses.

```
Week 1:  A A A B B B B
Week 2:  A A A A B B B
```

7 of 14 days each, four exchanges per cycle.

## What is a 5-2-2-5 schedule?

Five days, two, two, five. Like 2-2-5-5, it gives each parent consistent weekdays, with the long blocks placed differently.

```
Week 1:  A A A A A B B
Week 2:  A A B B B B B
```

## What is alternating weeks (week on, week off)?

Seven days with one parent, then seven with the other.

```
Week 1:  A A A A A A A
Week 2:  B B B B B B B
```

Two exchanges per cycle, the fewest of any equal-time schedule, which is one reason it often comes up in [parallel parenting](https://parallelparent.io/parallel-parenting) arrangements where handoffs are kept to a minimum. Each parent goes a full week without the child.

## What is an every-other-weekend schedule?

One parent has most days; the other has alternating weekends. The preset assumes the rotation starts on a Monday.

```
Week 1:  A A A A A B B
Week 2:  A A A A A A A
```

That is 12 days to 2. Plans often add a weekday dinner or a midweek overnight; add those as a [custom cycle](format.md#rotation) or as overrides.

## How do holidays fit on top of a rotation?

Most plans keep the regular rotation and then carve out holidays, which take precedence. The format handles this with **recurring overrides**:

- A **fixed date**: `{"month": 12, "day": 24}` for Christmas Eve.
- A **rule**: `{"month": 11, "weekday": "thursday", "nth": 4}` for Thanksgiving; `"nth": -1` means the last one in the month (Memorial Day is the last Monday of May).
- **Length and shift**: `"days": 5, "offset_days": -1` turns Thanksgiving into Wednesday through Sunday.
- **Alternation**: `"parent_even_years": "A", "parent_odd_years": "B"` swaps the holiday every year.

One-time changes, like a summer trip or an agreed swap, are **one-time overrides** and beat everything else. The full precedence is rotation, then recurring overrides, then one-time overrides.

## Which schedule is right?

That depends on the child's age, school, the distance between homes, and what a court has ordered. This project doesn't recommend one. It represents whichever schedule you already have, precisely, so it can be checked and shared.
