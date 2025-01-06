from django.db.models import QuerySet


class OrderingHelperOffers:
    @staticmethod
    def apply_ordering(queryset: QuerySet, ordering: str) -> QuerySet:
        """
        Applies the given ordering parameter to the queryset of offers.

        This method accepts a queryset of offers and an ordering parameter and
        returns the ordered queryset. The ordering parameter can have the
        following values:

            - "-created_at": Orders the offers by creation time in descending order.
            - "created_at": Orders the offers by creation time in ascending order.
            - "min_price": Orders the offers by their minimum price in ascending order.
            - "-min_price": Orders the offers by their minimum price in descending order.

        If the given ordering parameter is not one of the above, it defaults to
        "-created_at" (ordering by creation time in descending order).

        :param queryset: The queryset of offers to be ordered.
        :param ordering: The ordering parameter.
        :return: The ordered queryset of offers.
        """
        ordering_map = {
        "-created_at": "-created_at",
        "created_at": "created_at",
        "min_price": "min_price",
        "-min_price": "-min_price",
        "-updated_at": "updated_at",  
        "updated_at": "-updated_at",    
        }
        ordering_field = ordering_map.get(ordering, "-updated_at")  
        return queryset.order_by(ordering_field)