from rest_framework import serializers
from orders.models import Order


class OrdersListSerializer(serializers.ModelSerializer):
  class Meta:
    model = Order
    exclude = ['offer_detail_id']


class OrdersPostSerializer(serializers.ModelSerializer):
  class Meta:
    model = Order
    fields = ['offer_detail_id']


class OrderPatchSerializer(serializers.ModelSerializer):
  class Meta:
    model = Order
    fields = ['status']


  def update(self, instance, validated_data):
    """
    Updates an order instance with the given validated data.

    :param instance: The order instance to be updated.
    :param validated_data: The validated data to update the order with.
    :return: The updated order instance.
    """
    instance.status = validated_data.get('status', instance.status)
    instance.save()
    return instance



