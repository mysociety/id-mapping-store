# ID Mapping Store

This Django site provides an API for storing mappings between
different IDs.

Identifiers are scoped to particular "schemes"; e.g. a scheme
might represent GSS IDs in the UK, or Wikidata item IDs.

You can see all the schemes in the store with:

     curl 'http://localhost:8000/scheme'

... which might return:

    {
        "results": [
            {
                "id": 1,
                "name": "uk-area_id"
            },
            {
                "id": 2,
                "name": "wikidata-district-item"
            }
        ]
    }

To create new schemes, you can do that in the Django admin
interface at `/admin/`.

To associate two IDs from those schemes you can do:

    curl -X POST -H 'Content-Type: application/json' \
        'http://localhost:8000/equivalence-claim' \
        -d '{
                "identifier_a": {
                    "scheme_id": 1,
                    "value": "gss:S17000017"
                },
                "identifier_b": {
                    "scheme_id": 2,
                    "value": "Q1529479"
                }
             }'

To find all other IDs associated with a particular ID, you can
do the following:

    curl 'http://localhost:8000/identifier/1/gss:S17000017'

.... which might return:

    {
        "results": [
            {
                "scheme_name": "wikidata-district-item",
                "scheme_id": 2,
                "value": "Q1529479"
            }
        ],
        "history": [
            {
                "deprecated": false,
                "identifier": {
                    "scheme_name": "wikidata-district-item",
                    "scheme_id": 2,
                    "value": "Q1529479"
                },
                "created": "2018-01-12T18:18:25.315565+00:00"
            }
        ]
    }

Usually you will just want the identifiers under the `"results"`
key, which returns the identifiers currently believed to be
equivalent to the one specified in the URL path.

However, under the `"history"` key, you can find the history of
all identifiers that have been associated with the identifier
specified in the URL at any point: `"created"` shows when the
association was made, and `"deprecated"` shows whether it's
indicating a deprecation of that association.

Instead of using the scheme ID in the URL you can use the scheme
name instead (though we don't recommend this since schemes might
be renamed). For example:

    curl 'http://localhost:8000/identifier/uk-area_id/gss:S17000017'

... would return the same result.

Instead of deleting an ID mapping, you would post the same claim
but marking it as `deprecated`, e.g.:

    curl -X POST -H 'Content-Type: application/json' \
        'http://localhost:8000/equivalence-claim' \
        -d '{
                "identifier_a": {
                    "scheme_id": 1,
                    "value": "gss:S17000017"
                },
                "identifier_b": {
                    "scheme_id": 2,
                    "value": "Q1529479"
                },
                "deprecated": true
             }'

Then no ID would be returned under `"results"` afterwards for
either identifier; e.g.:

    curl 'http://localhost:8000/identifier/1/gss:S17000017'

... would then return:

    {
        "results": [],
        "history": [
            {
                "deprecated": false,
                "identifier": {
                    "scheme_name": "wikidata-district-item",
                    "scheme_id": 2,
                    "value": "Q1529479"
                },
                "created": "2018-01-12T18:18:25.315565+00:00"
            },
            {
                "deprecated": true,
                "identifier": {
                    "scheme_name": "wikidata-district-item",
                    "scheme_id": 2,
                    "value": "Q1529479"
                },
                "created": "2018-01-12T18:26:36.966097+00:00"
            }
        ]
    }
