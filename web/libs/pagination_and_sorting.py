import string
from typing import Text
from flask import request
from sqlalchemy import JSON

""" Pagination and sorting is performed here, add following to 
    endpoint: /?page=1&per_page=5&sort_by=id&sort_type=asc """

def paginate_and_sort(request: request, model: classmethod, schema: classmethod, payload_name: string, filter_by: JSON = {}) -> JSON:
    #Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 5, type=int)

    #Sort by desired key
    sort_by = request.args.get('sort_by', "id", type=Text)
    #Srot types: asc, desc
    sort_type = request.args.get('sort_type', "asc", type=Text)

    #paginated =  model.query.order_by(model.num_reservations.asc()).paginate(page, per_page, error_out=False)
    paginated =  model.query.filter_by(**filter_by).order_by(eval('model.'+sort_by+'.'+sort_type+'()')).paginate(page, per_page, error_out=False)

    #Return meta tag to make it easy for frontend
    meta = {
            "page": paginated.page,
            "pages": paginated.pages,
            "total_count": paginated.total,
            "prev_page": paginated.prev_num,
            "next_page": paginated.next_num,
            "has_next": paginated.has_next,
            "has_prev": paginated.has_prev,
    }

    return {payload_name: schema.dump(paginated.items), "meta": meta}, 200