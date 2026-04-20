# API Quick Reference

Base URL: `http://localhost:8000`

## Core Endpoints

- `POST /predict` or `POST /api/predict`
- `GET /weather` or `GET /api/weather`
- `GET /history` or `GET /api/history`

## Example: Predict by coordinates

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"location_name":"Fresno, US","latitude":36.7378,"longitude":-119.7871}'
```

## Example: Geocode

```bash
curl "http://localhost:8000/geocode?query=Sacramento"
```

## Example: Save pinned location

```bash
curl -X POST http://localhost:8000/api/saved-locations \
  -H "Content-Type: application/json" \
  -d '{"location_name":"Yosemite","latitude":37.8651,"longitude":-119.5383,"country_code":"US"}'
```
