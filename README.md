# Synthetic Tags

An easy way to retrieve values from CDF and execute mathematical operations on them at the same time.


## Motivation

To replace a custom-made structure like this:
``` python
{
    "EG_SecProd_Biocid": [
        ("EG_13FI1349L.Y", +1),
        ("EG_13FI1350L.Y", +1),
    ],
    "EG_PrimProd_Scale": [
        ("EG_13FI1318L.Y", "EG_13XV1322.Y", +1),
        ("EG_13FI1418L.Y", "EG_13XV1422.Y", +1),
        ("EG_13FI1518L.Y", "EG_13XV1522.Y", +1),
        ("EG_13FI1618L.Y", "EG_13XV1622.Y", +1),
        ...
```

with something more readable and powerful:

``` python
{
    "EG_SecProd_Biocid": Tag("EG_13FI1349L.Y") + Tag("EG_13FI1350L.Y"),
    "EG_PrimProd_Scale": (
        Tag("EG_13FI1318L.Y") * Tag("EG_13XV1322.Y") +
        Tag("EG_13FI1418L.Y") * Tag("EG_13XV1422.Y") +
        Tag("EG_13FI1518L.Y") * Tag("EG_13XV1522.Y") +
        Tag("EG_13FI1618L.Y") * Tag("EG_13XV1622.Y") +
        ...
```

Traditionally (by using Cognite SDK for Python), to retrieve a moderately complex set of data from CDF, we would:
 1. make a list of all the tags
 2. fetch from CDF and get a dataframe
 3. rename columns in the dataframe
 4. perform column-wise calculations
 5. perform any calculations specific to particular rows

With **Synthetic Tags** this becomes:
 1. define any custom column-wise calculations
 2. make a dict with specifications for columns (a single tag, or an expression involving multiple tags and functions)
 3. fetch and calculate in one step


## Advantages

### Expressive Syntax

``` python
>>> specs = {
...     "some_valve": Tag("FOO.123"),
...     "another_meter": Tag("BAR-456"),
...     "sum_of_2_things": Tag("THING_A") + Tag("THING_B"),
... }

>>> TagResolver(retrieval_function).latest(specs)
{
    "some_valve": 42.0000123,
    "another_meter": 42000.456000,
    "sum_of_2_things": 78.9,
}
```

`Tag` class is used as a reference for values that are going to be fetched from API. It "understands" many common
algebra operations such as:
 * basic math operations: `total_a_b = Tag("METER_A") + Tag("METER_B")`
 * parenthesis and literal values: `complicated_calculation = (Tag("METER_C") - 10) / (Tag("METER_D") + TAG("METER_E"))"`
 * boolean logic: `alert_status = Tag("METER_F") > 42`

It also supports function calls, either on multiple tags or on individual tags:
 * calculations on individual tags: `value_int = Tag("MEETER_G").calc(round)`
 * functions with multiple tags: `value_foo = Tag.apply(bar, Tag("MEETER_H"), Tag("MEETER_I"), Tag("MEETER_J"))`
   * `bar` is a function, see [Calculations with Multiple Tags](#calculations-with-multiple-tags) section below.


`TagResolver` is where the actual call to the API happens, and where `Tag` instances are replaced with actual values
and where math operations are performed. Besides `latest` there is also `resolve` and `df` (find more
info of all three below).



### Extendability

Easily extendable with additional function calls and / or math operations.

#### Calculations on a Single Tag

`Tag.calc` method takes a callable which will be applied to the result (element-wise) after the value has been fetched
from CDF.

``` python
>>> def galons_per_minute(val):
...     return val * 4.40287

>>> specs = {
...     "flow_in_sm3_per_hour": Tag("FLOW_METER.123"),
...     "flow_in_galons_per_minute": Tag("FLOW_METER.123").calc(galons_per_minute),
... }

>>> TagResolver(retrieval_function).latest(specs)
{
    "flow_in_sm3_per_hour": 12.3456,
    "flow_in_galons_per_minute": 54.35604149,
}
```

#### Calculations with Multiple Tags

`Tag.apply` is a class method that takes a callable and any number of `Tag` instances. When the values are fetched from
CDF, the callable will be applied (element-wise) with the tag values passed to it as arguments.

``` python
>>> def closest_to_42(*vals):
...     """Return whichever value in `vals` is closest to 42"""
...     deltas = [abs(42 - val) for val in vals]
...     return vals[deltas.index(min(deltas))]

>>> specs = {
...     "value_1": Tag("METER_A"),
...     "value_2": Tag("METER_B"),
...     "value_3": Tag("METER_C"),
...     "answer_to_everything": Tag.apply(closest_to_42, Tag("METER_A"), Tag("METER_B"), Tag("METER_C")),
... }
>>> TagResolver(retrieval_function).latest(specs)
{
    "value_1": 11,
    "value_2": 44,
    "value_3": 57,
    "answer_to_everything": 44,
}
```

##### `Tag.calc` is a Shorthand

`Tag.calc` is provided as a convenience method and for a more readable syntax.
It is equivalent to `Tag.apply` with a single argument:

``` python
# These two lines are equivalent:
Tag("FLOW_METER.123").calc(galons_per_minute)
Tag.apply(galons_per_minute, Tag("FLOW_METER.123"))
```

#### Referencing Functions by Name

Both `calc` and `apply` accept a string instead of a callable for their first argument. In this case, the string
must match a key in a dict passed to `TagResolver`. This dict contains the actual callables which are then used as
described above.

This feature can be used to address issues with importing Python modules, or to specify short functions using `lambda`.

``` python
>>> my_extension = {
...     "galons_per_minute": lambda val: return val * 4.40287,
... }

>>> specs = {
...     "flow_in_sm3_per_hour": Tag("FLOW_METER.123"),
...     "flow_in_galons_per_minute": Tag("FLOW_METER.123").calc("galons_per_minute"),
... }

>>> TagResolver(retrieval_function, my_extension).latest(specs)
{
    "flow_in_sm3_per_hour": 12.3456,
    "flow_in_galons_per_minute": 54.35604149,
}
```

``` python
>>> def closest_to_42(*vals):
...     """Return whichever value in `vals` is closest to 42"""
...     deltas = [abs(42 - val) for val in vals]
...     return vals[deltas.index(min(deltas))]

>>> specs = {
...     "value_1": Tag("METER_A"),
...     "value_2": Tag("METER_B"),
...     "value_3": Tag("METER_C"),
...     "answer_to_everything": Tag.apply("nearest_42", Tag("METER_A"), Tag("METER_B"), Tag("METER_C")),
... }

>>> TagResolver(retrieval_function, {"nearest_42": closest_to_42}).latest(specs)
{
    "value_1": 11,
    "value_2": 44,
    "value_3": 57,
    "answer_to_everything": 44,
}
```

### Caching and Combined API Calls

Any call to `TagResolver.latest` (or `df` or `resolve`) will result in the minimum number of calls
to the API to retrieves all needed values.

Each instance of `TagResolver` keeps internal cache and only queries the API for tags that are needed.

In the next example with multiple calls to `latest()`, the CDF time series API endpoint is hit only once.

``` python
>>> resolver = TagResolver(retrieval_function)

>>> resolver.latest({
...     "value_1": Tag("METER_A"),
...     "value_2": Tag("METER_B"),
...     "value_3": Tag("METER_C"),
...     "val_1_and_2": Tag("METER_A") + Tag("METER_B"),
...     "val_2_and_3": Tag("METER_B") + Tag("METER_C"),
...     "val_1_and_3": Tag("METER_A") + Tag("METER_C"),
... })
{"value_1": 12, "value_2": 23, "value_3": 34, "val_1_and_2": 35, "val_2_and_3": ...}

>>> resolver.latest({
...     "value_1": Tag("METER_A"),
...     "value_1_percent": 100 * Tag("METER_A") / (Tag("METER_A") + Tag("METER_B") + Tag("METER_C")),
... })
{"value_1": 12, "value_1_percent": 17.3913043478}

>>> resolver.latest({
...     "value_2": Tag("METER_B"),
...     "value_2_percent": 100 * Tag("METER_B") / (Tag("METER_A") + Tag("METER_B") + Tag("METER_C")),
... })
{"value_2": 23, "value_2_percent": 33.3333333333}
```


#### Avoiding Cache

In case that the caching is not desired (i.e. if we wanted to query CDF again in each of the three `latest()`
calls above) we should create a new instance of `TagResolver` for each one (i.e. use
`TagResolver(retrieval_function).latest` instead of `resolver.latest`).


## Multi-value Lookups (Series)

While the primary motivation for **Synthetic Tags** library was to facilitate single-value lookups, as seen in the
examples so far, the library also supports retrieving of multiple datapoints per tag (as `pd.Series`) as well as
performing element-wise operations on them.

See "Full examples" section below for more examples with Series.


## Multiple Data Stores

`Tag` class supports specifying a string key for an alternative data store (a.k.a. the fetch function).
The corresponding argument has to be present in the `TagResolver` constructor call. This allows us to mix
and match values from tags obtained from separate CDF API calls.

For example, we can fetch a single average value of a time series and then multiply it with a series of values from
another time series (or, indeed, the same one if desired):

``` python
>>> resolver = TagResolver(get_series, average=get_average)

>>> resolver.latest({
...     "avg_value": Tag("METER_A", "average"),
...     "above_average": Tag("METER_A") > Tag("METER_A", "average"),
... })
{
    "avg_value": 42,
    "above_average: <pd.Series... >,  # series of bool values, True for points that are above 42, False for others
}
```

Note: All tags using any particular value store are gathered in a single API call, so no matter how many tags there are,
the number of calls to the CDF API will always be equal to the number of value stores.

There are two caveats to this:
 1. Any value stores that don't have any tags are not used, i.e. no calls there.
 2. For really large number of tags, the CDF SDK might split up a single large query into multiple smaller queries
    that it executes in parallel and then combines the results of. This is an internal implementation detail of
    the Python CDF SDK and does not affect (not is being affected) by **Cognite Synthetic Tags**.


## Limitations

### Boolean expressions

Python does not allow overloading boolean operations, so `bool(Tag(...))` is not allowed (it will raise a `ValueError`
with an extensive explanation.)

This is because expressions like `Tag(A) or Tag(B)` get evaluated immediately, there is no (good) way to defer the
evaluation until values have been fetched from CDF.

#### Use Bit-wise Operators

Expressions like `Tag(A) | Tag(B)` work as expected.

Full list of bit-wise operators:
 - `and`: `&`
 - `or`: `|`
 - `xor`: `^`
 - `not`: `~`


#### Don't Use Ternary Operator

Because of the limitations discussed here, there is no way to use ternary operator with instances of `Tag` class:

``` python
specs = {
    "foo": Tag(A) if Tag(A) > 0 else Tag(B),  # will not work!
}
````

Instead, define a custom operation and use `Tag.apply` to apply it:
``` python
def positive_a_or_b(a, b):
    return a if a > 0 else b

specs = {
    "foo": Tag.apply(positive_a_or_b, Tag(A), Tag(B)),
}
```


## Comparison with Synthetic Time Series API

CDF API supports
[Synthetic Time Series](https://docs.cognite.com/dev/concepts/resource_types/synthetic_timeseries.html). This library
provides similar functionality and there is a significant overlap (e.g. both can apply trigonometric functions on
CDF values).

The main difference is that Synthetic Time Series performs calculations on the server, whereas **Synthetic Tags**
fetches only basic data from the API and performs the calculations locally.

Performing the calculations serverside means less code and fewer opportunities for bugs.

Performing the calculations locally means more control and extendability.

In principle some support for the Synthetic Time Series API could be added to this library. TDB.


## Full Examples

This section uses data from OpenIndustrialData project.

Env for these examples:
``` bash
COGNITE_PROJECT='publicdata'
COGNITE_CLIENT_NAME='testing_synth_tags'  # anything
COGNITE_API_KEY='<API_KEY>'
```

Get your API key from https://openindustrialdata.com/get-started/

#### Imports and Data Storage Callable

``` python
>>> from cognite_synthetic_tags import point_at_time, series, Tag, TagResolver
>>> from cognite.client import CogniteClient

>>> # CONFIGURE FETCHING PARAMS:

>>> client = CogniteClient()
>>> get_latest = point_at_time(
...     client,
...     query_by="external_id",
...     at_time="90d-ago",
...     lookbehind_start_time="91d-ago",
... )

>>> get_average = point_at_time(
...     client,
...     query_by="external_id",
...     at_time="90d-ago",
...     lookbehind_limit=10,
...     aggregate="average",
...     granularity="1h",
... )

>>> get_series = series(
...     client,
...     query_by="external_id",
...     start="91d-ago",
...     end="90d-ago",
...     aggregate="average",
...     granularity="1h",
... )

>>> # just for readability:
>>> VALVE_22 = "houston.ro.REMOTE_AI[22]"
>>> METER_A = "houston.ro.REMOTE_AI[3]"
>>> METER_B = "houston.ro.REMOTE_AI[4]"
>>> METER_C = "houston.ro.REMOTE_AI[5]"
```

#### Simple Usage

``` python
>>> # single value (not very useful):
>>> tag_resolver = TagResolver(get_latest)
>>> specs = {"valve": Tag(VALVE_22)}
>>> tag_resolver.series(specs)
{'valve': 0.003925000131130218}
```
``` python
>>> # simple multiplication:
>>> specs = {"valve_percent": 100 * Tag(VALVE_22)}
>>> tag_resolver.series(specs)
{'valve_percent': 39.25000130113021085}
```
``` python
>>> # apply a function to a value:
>>> specs = {"valve_percent_int": (100 * Tag(VALVE_22)).calc(round)}
>>> tag_resolver.series(specs)
{'valve_percent_int': 39}
```

> Notice in the last example we cal `calc` on the result of `100 * Tag(...)`. This works because whenever  a `Tag`
> instance encounters a math operator, it combines with other operands (the liberal value `100` in this example) to
> create a new `Tag` instance. We have called `calc` method on this new `Tag` instance.

``` python
>>> # fetch multiple values in a single API call and also perform some math:
>>> specs = {
...     "pressure_1": Tag(METER_A),
...     "pressure_2": Tag(METER_B),
...     "pressure_diff": Tag(METER_A) - Tag(METER_B),
...     "p1_percent": Tag(METER_A) / (Tag(METER_A) + Tag(METER_B)) * 100,
... }
>>> tag_resolver.series(specs)
{'pressure_1': 1.4,
 'pressure_2': 35.8,
 'pressure_diff': -34.4,
 'p1_percent': 3.763440860215054}
```

#### Usage with Series

``` python
>>> specs = {"valve": Tag(VALVE_22)}
>>> tag_resolver = TagResolver(get_series)
>>> tag_resolver.series(specs)
{'valve': 2021-06-16 17:21:08    0.239425
          2021-06-16 17:21:09    1.350200
          2021-06-16 17:21:10    2.743576
          2021-06-16 17:21:11    3.544276
          2021-06-16 17:21:12    3.873974
          2021-06-16 17:21:14    4.254700
          2021-06-16 17:21:15    4.509826
          2021-06-16 17:21:16    4.662900
          2021-06-16 17:21:17    4.702150
          2021-06-16 17:21:18    4.706076
          Name: houston.ro.REMOTE_AI[22], dtype: float64,
}
```
> The value under key `"valve"` in the output above is an instance of `pandas.Series`, indented for readability.

## Advanced Usage

### Custom function calls on single Tag value

``` python
>>> custom_operations = {
...     "md5": lambda a: hashlib.md5(str(a).encode()).hexdigest(),
... }
>>> tag_resolver = TagResolver(get_latest, custom_operations)

>>> specs = {
...     "pressure": Tag(METER_A),
...     "pressure_md5": Tag(METER_B).calc("md5"),
... }
>>> tag_resolver.series(specs)
{'pressure': 4.15, 'pressure_md5': '7fd3...'}
```


### Custom function calls on multiple Tag values

``` python
>>> custom_operations = {"max": max, "sum": lambda *vals: sum(vals)}
>>> tag_resolver = TagResolver(get_latest, custom_operations)

>>> specs = {
...     "pressure_1": Tag(METER_A),
...     "pressure_2": Tag(METER_B),
...     "pressure_3": Tag(METER_C),
...     "pressure_highest": Tag.apply("max", Tag(METER_A), Tag(METER_B), Tag(METER_C)),
...     "highest_to_total_ratio": (
...         Tag.apply("max", Tag(METER_A), Tag(METER_B), Tag(METER_C))
..          / Tag.apply("sum", Tag(METER_A), Tag(METER_B), Tag(METER_C))
...     ),
... }
>>> tag_resolver.series(specs)
{'pressure_1': 30.95,
 'pressure_2': 19.1,
 'pressure_3': 20.05,
 'pressure_highest': 30.95,
 'highest_to_total_ratio': 0.4415121255349501}
```

### Operations on Series

This example below is intentionally as similar as possible to the previous example. The only difference is the retrieval
function passed to `TagResolver`: `get_series` in this example vs `get_latest` in the previous one.

> See definition of `get_series` and `get_latest` at the start of [Full Examples](#full-examples) section above.

``` python
>>> custom_operations = {"max": max, "sum": lambda *vals: sum(vals)}
>>> tag_resolver = TagResolver(get_series, custom_operations)

>>> specs = {
...     "pressure_1": Tag(METER_A),
...     "pressure_2": Tag(METER_B),
...     "pressure_3": Tag(METER_C),
...     "pressure_highest": Tag.apply("max", Tag(METER_A), Tag(METER_B), Tag(METER_C)),
...     "highest_to_total_ratio": (
...         Tag.apply("max", Tag(METER_A), Tag(METER_B), Tag(METER_C))
..          / Tag.apply("sum", Tag(METER_A), Tag(METER_B), Tag(METER_C))
...     ),
... }
>>> tag_resolver.series(specs)
{'pressure_1': 2021-06-16 17:23:37    48.30
               2021-06-16 17:23:38    48.25
               2021-06-16 17:23:39    48.15
               ...
               Name: houston.ro.REMOTE_AI[3], dtype: float64,
 'pressure_2': 2021-06-16 17:23:37    42.30
               2021-06-16 17:23:38    42.10
               2021-06-16 17:23:39    42.10
               ...
               Name: houston.ro.REMOTE_AI[4], dtype: float64,
 'pressure_3': 2021-06-16 17:23:37    119.95
               2021-06-16 17:23:38    120.20
               2021-06-16 17:23:39    120.10
               ...
               Name: houston.ro.REMOTE_AI[5], dtype: float64,
 'pressure_highest': 2021-06-16 17:23:37     119.95
                     2021-06-16 17:23:38     120.20
                     2021-06-16 17:23:39     120.10
                     ...
                     dtype: float64,
 'highest_to_total_ratio': 2021-06-16 17:23:37     0.569698
                           2021-06-16 17:23:38     0.570886
                           2021-06-16 17:23:39     0.570953
                           ...
                           dtype: float64,
}
```
> The value in the output dicts above are instances of `pandas.Series`, indented and trimmed for readability.


### But, where are the DataFrames?!

Results from `TagResolver.resolve` can be passed directly to `pd.DataFrame` to get the expected dataframe.

This is a natural fit for series results, e.g:

``` python
>>> # ...continuing from the previous example
>>> data = tag_resolver.series(specs)
>>> pd.DataFrame(data)
                     pressure_1  pressure_2  pressure_3  pressure_highest  highest_to_total_ratio
2021-06-16 17:42:50       49.65       39.55      139.10            139.10                0.609286
2021-06-16 17:42:51       49.85       39.80      138.70            138.70                0.607401
2021-06-16 17:42:53       49.50       39.45      138.50            138.50                0.608925
...
```

For single-value responses, the DataFrame will have a single row, and the call to `pd.DataFrame` will require an index
in addition to the data dict:

``` python
>>> data = {   # from a previous example
...     'pressure_1': 30.95,
...     'pressure_2': 19.1,
...     'pressure_3': 20.05,
...     'pressure_highest': 30.95,
...     'highest_to_total_ratio': 0.4415121255349501,
... }
>>> pd.DataFrame(data, index=[0])  # [0] or any one-element iterable
   pressure_1  pressure_2  pressure_3  pressure_highest  highest_to_total_ratio
0       30.95        19.1       20.05             30.95                0.441512
```

### Multiple Data Stores

``` python
>>> specs = {
...     "avg_value": Tag(METER_A, "average"),
...     "above_average": Tag(METER_A) > Tag(METER_A, "average"),
... }
>>> resolver = TagResolver(get_series, average=get_average)
>>> resolver.series(specs)
{
    "avg_value": 42,
    "above_average: <pd.Series of bool values, True for points that are above 42, False for others>,
}
```

Responses with mixed single-value and multi-value items can also be passed into `pd.DataFrame` constructor. Pandas
will automatically repeat any single-value items across all rows in the new dataframe.

If using multiple data store function, the results will likely have different indexes. `pd.DataFrame` constructor will
create a new dataframe with a combined index. This can result in a sparsely filled dataframe (many cells having `np.nan`
value).

#### More complex example

To expand on the previous example, let us require the difference between average value and any actual value, but
only if the value is above average, otherwise set it to 0. For example, this is a dataframe that we want to get:
```
                          value   avg_value   above_average  positive_diff
2021-06-16 17:42:10       49.65       43.21            True        6.43999
2021-06-16 17:42:20       44.85       43.21            True        1.64000
2021-06-16 17:42:30       41.50       43.21           False              0
2021-06-16 17:42:40       40.90       43.21           False              0
2021-06-16 17:42:50       41.50       43.21           False              0
2021-06-16 17:42:60       43.30       43.21            True       0.089999
...
```

There are many ways to get this result, here are a few equivalent ones.

``` python
specs = {
   "value": Tag(METER_A),
   "avg_value": Tag(METER_A, "average"),
   "above_average": Tag(METER_A) > Tag(METER_A, "average"),
   "positive_diff": (Tag(METER_A) - Tag(METER_A, "average")) if Tag(METER_A) > Tag(METER_A, "average") else 0,
}
```

``` python
def positive_or_0(val):
    return val if val > 0 else 0

specs = {
   "value": Tag(METER_A),
   "avg_value": Tag(METER_A, "average"),
   "above_average": Tag(METER_A) > Tag(METER_A, "average"),
   "positive_diff": (Tag(METER_A) - Tag(METER_A, "average")).calc(positive_or_0),
}
```

``` python
avg_spec = Tag(METER_A, "average")
meter_spec = Tag(METER_A)
above_spec = meter_spec > avg_spec
diff_spec = meter_spec - avg_spec
positive_diff_spec = diff_spec if above_spec else 0

specs = {
   "value": meter_spec,
   "avg_value": avg_spec,
   "above_average": above_spec,
   "positive_diff": positive_diff_spec,
}
```


## Provided Data Stores

All examples in this document use data stores (a.k.a. retrieval functions) that are provided in
`cognite_synthetic_tags.data_stores` module. These are prepared to work with `TagResolver`.

Provided stores:
 * `series` - returns multiple values for every tag, as `pd.Series` instances.
 * `point` - same as `series` except that it returns only the last point in each series.
 * `series_at_time` - same as `series` except it takes `at_time` and `lookbehind_start_time` as an alternative
    to `end` and `start` arguments.
 * `point_at_time` - same as  `point` except it takes `at_time` and `lookbehind_start_time` as an alternative
    to `end` and `start` arguments.

Check docstrings for more details.


## TODO

 * Add better support for passing lambdas to `calc` an `apply`, e.g. `Tag(..).calc(some_value=lambda val: val + 42)`
 * Internally **Synthetic Tags** is using `DataFrame` and `Series` from Pandas. There is a small performance penalty
   associated with this, so we should probably make the effort to work directly with response objects from Cognite SDK.
 * Check the effects of `include_outside_points` on the provided data store functions.
