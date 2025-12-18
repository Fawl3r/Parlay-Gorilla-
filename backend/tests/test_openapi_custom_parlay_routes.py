from app.main import app


def test_openapi_custom_parlay_analyze_expects_json_body():
    spec = app.openapi()
    op = spec["paths"]["/api/parlay/analyze"]["post"]

    # Must be a JSON body containing the CustomParlayRequest schema
    assert "requestBody" in op
    schema = op["requestBody"]["content"]["application/json"]["schema"]
    assert schema.get("$ref", "").endswith("/CustomParlayRequest")

    # Guard against regression where the model is treated as a query param (422: query.parlay_request missing)
    params = op.get("parameters", []) or []
    assert not any(p.get("in") == "query" and p.get("name") == "parlay_request" for p in params)




