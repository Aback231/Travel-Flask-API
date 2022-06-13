from werkzeug.security import safe_str_cmp
from typing import Text
import config

from constants.user_roles import UserRoles
from constants.http_status_codes import HTTP_200_OK, HTTP_400_BAD_REQUEST


PAGINATION_ERROR = ("Pagination failed. Error: {}")


def paging(request):
    """ Extract pagination variables from request params """
    # Pagination variables
    page = request.args.get('page', config.DEFAULT_PAGE, type=int)
    per_page = request.args.get('per_page', config.ITEMS_PAGE, type=int)

    # Sort by desired key
    sort_by = request.args.get('sort_by', config.DEFAULT_TAG, type=Text)
    # Srot types: asc, desc
    sort_type = request.args.get('sort_type', config.DEFAULT_SORT_TYPE, type=Text)

    return {"page": page, "per_page": per_page, "sort_by": sort_by, "sort_type": sort_type}


def meta_tag(paginated):
    """ Return meta tag to make it easy for frontend """
    meta = {
        "page": paginated.page,
        "pages": paginated.pages,
        "total_count": paginated.total,
        "prev_page": paginated.prev_num,
        "next_page": paginated.next_num,
        "has_next": paginated.has_next,
        "has_prev": paginated.has_prev,
    }
    return meta


def paginate_and_sort(request, model, schema, payload_name, filter_by={}):
    """ Pagination and sorting is performed here, add following to 
    endpoint: /?page=1&per_page=5&sort_by=id&sort_type=asc """
    """ Used for all function performing listings. """
    try:
        pg = paging(request)

        paginated =  model.query.filter_by(**filter_by).order_by(eval('model.'+pg["sort_by"]+'.'+pg["sort_type"]+'()')).paginate(pg["page"], pg["per_page"], error_out=False)

        meta = meta_tag(paginated)

        return {payload_name: schema.dump(paginated.items), "meta": meta}, HTTP_200_OK
    except Exception as e:
            return {"message": PAGINATION_ERROR.format(e)}, HTTP_400_BAD_REQUEST


def paginate_sort_filter_user_profiles(request, model, schema, payload_name, filter_by):
    """ Used for UserProfileList, to list all user profiles, including reservations and tour guides.  """
    try:
        pg = paging(request)
        acc_filter = request.args.get('filter', type=Text)

        if not acc_filter:
            paginated =  model[0].query.filter((model[0].acc_type == filter_by[0]) | (model[0].acc_type == filter_by[1])).order_by(eval('model[0].'+pg["sort_by"]+'.'+pg["sort_type"]+'()')).paginate(pg["page"], pg["per_page"], error_out=False)
        else:
            paginated =  model[0].query.filter((model[0].acc_type == acc_filter)).order_by(eval('model[0].'+pg["sort_by"]+'.'+pg["sort_type"]+'()')).paginate(pg["page"], pg["per_page"], error_out=False)

        meta = meta_tag(paginated)

        items = schema[0].dump(paginated.items)
        for item in items:
            if safe_str_cmp(item["acc_type"], UserRoles.TOURIST.value):
                item["arrangement_reservations"] = schema[1].dump(model[0].find_by_id(item["id"]).arrangements_reservations)
            else:
                item["tour_guide_bookings"] = schema[1].dump(model[1].find_all_by_tour_guide_id(item["id"]))
            
        return {payload_name: items, "meta": meta}, HTTP_200_OK
    except Exception as e:
            return {"message": PAGINATION_ERROR.format(e)}, HTTP_400_BAD_REQUEST