from odoo import http
from odoo.http import request
import requests


class LocationController(http.Controller):


    @http.route('/custom/location/fetch_location_data', type="jsonrpc", auth='user')
    def fetch_location_data(self, latitude, longitude):
        try:
            url = "https://nominatim.openstreetmap.org/reverse"

            headers = {
                "User-Agent": "Odoo19-CustomLocation/1.0"
            }

            params = {
                "lat": latitude,
                "lon": longitude,
                "format": "json",
                "zoom": 18,
                "addressdetails": 1
            }

            response = requests.get(url, headers=headers, params=params, timeout=5)

            print("STATUS:", response.status_code, response)

            if response.status_code != 200:
                return {"error": f"Geocoding failed: {response.status_code}"}

            data = response.json()
            address = data.get('address', {})
            print('--------------------------', data)
            street = (
                    address.get('road')
                    or address.get('pedestrian')
                    or address.get('neighbourhood')
                    or ''
            )

            city = (
                    address.get('city')
                    or address.get('town')
                    or address.get('village')
                    or ''
            )

            return {
                'display_name': data.get('display_name', ''),
                'address': {
                    'street': street,
                    'street2': address.get('suburb', ''),
                    'city': city,
                    'state': address.get('state', ''),
                    'country': address.get('country', ''),
                    'pincode': address.get('postcode', ''),
                }
            }
        except Exception as e:
            return {'error': str(e)}

    @http.route('/custom/location/update_location', type="jsonrpc", auth='user')
    def update_location(self, **kwargs):

        latitude = kwargs.get("latitude")
        longitude = kwargs.get("longitude")
        address = kwargs.get("address", {})
        city = kwargs.get("city")
        state = kwargs.get("state")
        country = kwargs.get("country")
        pincode = kwargs.get("pincode")
        active_id = kwargs.get("active_id")
        model = kwargs.get("model")

        if not active_id or not model:
            return {"success": False, "error": "Missing data"}

        record = request.env[model].browse(active_id)

        if not record.exists():
            return {"success": False, "error": "Record not found"}

        # 🔥 If model is property or building → get its location_id
        if hasattr(record, "location_id") and record.location_id:
            location = record.location_id
        else:
            # fallback if directly custom.location
            location = record

        location.write({
            'name': f'{latitude},{longitude}',
            'street': address.get('street', ''),
            'street2': address.get('street2', ''),
            'city': city,
            'state': state,
            'country': country,
            'pincode': pincode,
        })

        return {'success': True, 'location_id': location.id}
