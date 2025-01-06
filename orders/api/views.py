from rest_framework.views import APIView
from orders.models import Order
from .serializers import OrdersListSerializer, OrdersPostSerializer, OrderPatchSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User


class OrdersListAPIView(APIView):
  permission_classes = [IsAuthenticatedOrReadOnly]
  def get(self, request, format=None):
    orders = Order.objects.all()
    serializer = OrdersListSerializer(orders, many=True)
    return Response(serializer.data)
  
  def post(self, request, format=None):
        serializer = OrdersPostSerializer(data=request.data)
        if serializer.is_valid():
            # Pass request.user.id as the user when saving
            serializer.save(customer_user=request.user.id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


class SingleOrderAPIView(APIView):
  permission_classes = [IsAuthenticatedOrReadOnly]
  def get(self, request, pk, format=None):
    order = Order.objects.get(pk=pk)
    serializer = OrdersListSerializer(order)
    return Response(serializer.data)
  
  def patch(self, request, pk, format=None):
    # Retrieve the specific order
    order = get_object_or_404(Order, pk=pk)

    # Check permissions
    is_creator = order.business_user == request.user
    is_admin = request.user.is_staff
    if not (is_creator or is_admin):
        return Response(
            {"detail": ["Sie sind nicht berechtigt, diese Bestellung zu ändern."]},
            status=status.HTTP_403_FORBIDDEN
        )

    # Use OrderPatchSerializer for partial update
    serializer = OrderPatchSerializer(order, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()

        # Use a different serializer (e.g., OrdersListSerializer) for the full response
        full_serializer = OrdersListSerializer(order)
        return Response(full_serializer.data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
  

  def delete(self, request, pk, format=None):
    if not (request.user.is_staff):
        return Response(
            {"detail": ["Sie sind nicht berechtigt, diese Bestellung zu löschen."]},
            status=status.HTTP_403_FORBIDDEN
        )
    order = get_object_or_404(Order, pk=pk)
    order.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
  

class OrdersBusinessUncompletedCountAPIView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    def get(self, request, pk, format=None):
        try:
            business_user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"detail": ["Diesen Business User gibt es nicht."]}, status=status.HTTP_404_NOT_FOUND)
        orders = Order.objects.filter(business_user=business_user).exclude(status='completed')
        return Response({"order_count": orders.count()})


class OrdersBusinessCompletedCountAPIView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    def get(self, request, pk, format=None):
        try:
            business_user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"detail": ["Diesen Business User gibt es nicht."]}, status=status.HTTP_404_NOT_FOUND)

        orders = Order.objects.filter(business_user=business_user, status='completed')
        return Response({"completed_order_count": orders.count()})

