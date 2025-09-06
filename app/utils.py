def paginate(total: int, page: int, limit: int):
    pages = (total + limit - 1) // limit if limit else 1
    return {
        "page": page,
        "limit": limit,
        "pages": pages,
        "total": total,
        "has_next": page < pages,
        "has_prev": page > 1,
    }
