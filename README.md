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

## Advantages

### Expressive Syntax

`Tag` class is used as a reference for values that are going to be fetched from API.

`TagResolver` is where the actual call to the API happens, and where `Tag` instances are replaces with actual values
and math operations are performed.

``` python
>>> specs = {
...     "some_valve": Tag("FOO.123"),
...     "another_metetr": Tag("BAR.456"),
...     "sum_of_2_things": Tag("THING.A") + Tag("THING.B"),
... }
>>> TagResolver(retrival_function).resolve(specs)
{
    "some_valve": 42.0000123,
    "another_metetr": 42000.456000,
    "sum_of_2_things": 78.9,
}
```

### Extendability

Easily extendable with additional function calls and / or math operations.
`TagResolver` takes a second argument, `additional_operation`, a dict with callables that can be used in expressions:

``` python
>>> my_extension = {"galons_per_minute": lambda val: val * 4.40287}
>>> specs = {
...     "flow_in_sm3_per_hour": Tag("FLOW_METER.123"),
...     "flow_in_galons_per_minute": Tag("FLOW_METER.123").calc("galons_per_minute"),
... }
>>> TagResolver(retrival_function, my_extension).resolve(specs)
{
    "flow_in_sm3_per_hour": 12.3456,
    "flow_in_galons_per_minute": 54.35604149,
}
```

It is also possible to use functions that take multiple values:

``` python
>>> def closest_to_42(*vals):
...     deltas = [abs(42 - val) for val in vals]
...     return vals[deltas.index(min(deltas))]

>>> my_extension = {"nearest_42": closest_to_42}
>>> specs = {
...     "value_1": Tag("METER_A"),
...     "value_2": Tag("METER_B"),
...     "value_3": Tag("METER_C"),
...     "answer_to_everything": Tag.call("nearest_42", Tag("METER_A"), Tag("METER_B"), Tag("METER_C")),
... }
>>> TagResolver(retrival_function, my_extension).resolve(specs)
{
    "value_1": 11,
    "value_2": 44,
    "value_3": 57,
    "answer_to_everything": 44,
}
```

### Caching and Combined API Calls

Any call to `TagResolver.resolve` will result in only one call to the API that retrieves all needed values.

Each instance of `TagResolver` keeps internal cache and only queries the API for tags that are needed.

In the next example, the CDF time series API endpoint is hit only once with a query for 3 time series.

``` python
>>> resolver = TagResolver(retrival_function)
>>> resolver.resolve({
...     "value_1": Tag("METER_A"),
...     "value_2": Tag("METER_B"),
...     "value_3": Tag("METER_C"),
...     "val_1_and_2": Tag("METER_A") + Tag("METER_B"),
...     "val_2_and_3": Tag("METER_B") + Tag("METER_C"),
...     "val_1_and_3": Tag("METER_A") + Tag("METER_C"),
... })
{"value_1": 12, "value_2": 23, "value_3": 34, "val_1_and_2": 35, "val_2_and_3": ...}
>>> resolver.resolve({
...     "value_1": Tag("METER_A"),
...     "val_1_percent": 100 * Tag("METER_A") / (Tag("METER_A") + Tag("METER_B") + Tag("METER_C")),
... })
{"value_1": 12, "value_1_percent": 17,3913043478}
>>> resolver.resolve({
...     "value_2": Tag("METER_B"),
...     "val_2_percent": 100 * Tag("METER_B") / (Tag("METER_A") + Tag("METER_B") + Tag("METER_C")),
... })
{"value_1": 23, "value_1_percent": 33,3333333333}
```

To avoid having values cached like this, use a new instance of `TagResolver` for each query.


## Limitations

### Single-value lookups

For now, this library works only for retrieving single values from CDF. As such it can be used as-is to fetch:
 * most recent values from time series
 * most recent aggregated values from time series.

It does not support retrieving multiple time series.

In principle, there is no reason why we couldn't use the same approach to fetch (and perform math and other operations)
on time series. It just has not been implemented yet.


### Single data storage

For now `TagResolver` class supports a single callable that it uses to fetch the values. This means that we can use it
to (for example) fetch average values or max values, but we cannot "mix and match". In other words, it is not possible
to use different API parameters when fetching different tags in a single call:

``` python
>>> resolver.resolve({
...     "avg_value": Tag("FOO"),  # if "FOO" is uses "average" aggregation, then "BAR" also has to (e.g. cannot use max)
...     "max_value": Tag("BAR"),
... })

```

This could be implemented by adding support for multiple `data_storage` callables on `TagResolver`:

``` python
>>> resolver = TagResolver({"avg": average_data_store_func, "max": max_data_store_func})  # NOT IMPLEMENTED!
>>> resolver.resolve({
...     "avg_value": Tag("FOO", data_store="avg"),  # NOT IMPLEMENTED!
...     "max_value": Tag("BAR", data_store="max"),  # NOT IMPLEMENTED!
... })
```


Note: This limitation only applies to a single `TagResolver.resolve` call. There is no issue with using two separate
`TagResolver` instances, each with different `data_store` callable.

## Comparison with Synthetic Time Series API

CDF API supports
[Synthetic Time Series](https://docs.cognite.com/dev/concepts/resource_types/synthetic_timeseries.html). This library
provides similar functionality and there is a significant overlap (e.g. both can apply trigonometric functions on CDF).

The main difference is that Synthetic Time Series performs calculations on the server, whereas this library fetches
only basic data from the API and performs the calculations locally.

Performing the calculations serverside means less code and opportunity for bugs.

Performing them locally means more control and extendability.

In principle some support for the Synthetic Time Series API could be added to this library. TDB.


## Example Uses

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
>>> from cognite_synthetic_tags import latest_datapoint, Tag, TagResolver
>>> from cognite.client import CogniteClient

>>> # CONFIGURE FETCHING PARAMS:

>>> client = CogniteClient()
>>> def retrival_call(tags):
...     return latest_datapoint(
...         client,
...         query_by="external_id",
...         start="90d-ago",
...         end="89d-ago",
...         # agregate="average",  # if we wanted to use an agregate
...     )(tags)
>>> tag_resolver = TagResolver(retrival_call)
```

#### Simple Usage

``` python

>>> # single value (not very useful):
>>> specs = {"valve": Tag("houston.ro.REMOTE_AI[22]")}
>>> tag_resolver.resolve(specs)
{'valve': 0.003925000131130218}

>>> # simple multiplication:
>>> specs = {"valve_percent": 100 * Tag("houston.ro.REMOTE_AI[22]")}
>>> tag_resolver.resolve(specs)
{'valve': 39.25000130113021085}


>>> # fetch multiple values in a single API call and also perform some math:
>>> METER_A = "houston.ro.REMOTE_AI[3]"  # just for readability...
>>> METER_B = "houston.ro.REMOTE_AI[4]"
>>> specs = {
...     "pressure_1": Tag(METER_A),
...     "pressure_2": Tag(METER_B),
...     "pressure_diff": Tag(METER_A) - Tag(METER_B),
...     "p1_percent": Tag(METER_A) / (Tag(METER_A) + Tag(METER_B)) * 100,
... }
>>> tag_resolver.resolve(specs)
{'pressure_1': 1.4,
 'pressure_2': 35.8,
 'pressure_diff': -34.4,
 'p1_percent': 3.763440860215054}
```

## Advanced Usage

### Custom function calls on single Tag value

``` python
>>> custom_operations = {
...     "md5": lambda a: hashlib.md5(str(a).encode()).hexdigest(),
... }
>>> tag_resolver = TagResolver(retrival_call, custom_operations)

>>> specs = {
...     "pressure": Tag(METER_A),
...     "pressure_md5": Tag(METER_B).calc("md5"),
... }
>>> tag_resolver.resolve(specs)
{'pressure': 4.15, 'pressure_md5': '7fd3...'}
```


### Custom function calls on multiple Tag values

``` python
>>> custom_operations = {"max": max, "sum": sum}  # these are builtins, but we can use any callables that take *args
>>> tag_resolver = TagResolver(retrival_call, custom_operations)

>>> METER_C = "houston.ro.REMOTE_AI[5]"
>>> specs = {
...     "pressure_1": Tag(METER_A),
...     "pressure_2": Tag(METER_B),
...     "pressure_3": Tag(METER_C),
...     "pressure_highest": Tag.call("max", Tag(METER_A), Tag(METER_B), Tag(METER_C)),
...     "highest_to_total_ratio": (
...         Tag.call("max", Tag(METER_A), Tag(METER_B), Tag(METER_C))
..          / Tag.call("sum", Tag(METER_A), Tag(METER_B), Tag(METER_C))
...     ),
... }
>>> tag_resolver.resolve(specs)
{'pressure_1': 30.95,
 'pressure_2': 19.1,
 'pressure_3': 20.05,
 'pressure_highest': 30.95,
 'highest_to_total_ratio': 0.4415121255349501}
```
