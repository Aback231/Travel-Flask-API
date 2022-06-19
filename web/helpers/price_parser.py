import config


def price_calculation(nr_reservations: int, price: float) -> float:
    """ Calculate price sum with discount for arrangement reservation """
    price_sum = nr_reservations * price
    if nr_reservations > config.DISCOUNT_RESERVATIONS_TRESHOLD:
        price_sum = price_sum - (nr_reservations - config.DISCOUNT_RESERVATIONS_TRESHOLD) * (price * config.DISCOUNT_PERCENTAGE/100)
    return price_sum