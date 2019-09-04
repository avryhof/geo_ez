# Geo EZ
```bash
pip install geo_ez
```

A reusable Django module for building Gographically aware applications without needing to install a real GIS backend.

## settings.py
```python
INSTALLED_APPS=[
    "...",
    "gis",
    "..."
]
```

## Management commands

This will create the database tables for the models, and import US Postal Codes from GeoNames.

```bash
manage.py migrate
manage.py import-postal-codes
```

## Now you can
- Extend the GISPoint model to build your own objects with stored corrdinates.
- Extend the StreetAddress model to have coordinate-aware street addresses in your own models.

Any model Extended from GISPoint (Which includes any model extended from StreetAddress) can now be interacted with like this.A

```python
class GeoCache(GISPoint):
    gc_id = CharField(max_length=20)


cache = GeoCache.objects.get(gc_id='GC12345')
cache.distance_from(-76.123456, 43.123456, 5) # latitude, longitude, radius_in_miles
                                              # - radius can also be in km if the keyword argument use_miles=False

cache.in_radius(-76.123456, 43.123456, 5) # latitude, longitude, radius_in_miles
                                          # - radius can also be in km if the keyword argument use_miles=False

caches = points_within_radius(GeoCache, -76.123456, 43.123456, radius=5, use_miles=True)

```
