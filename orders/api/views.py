from rest_framework.views import APIView
from orders.models import Order
from .serializers import OrdersListSerializer, OrdersPostSerializer, OrderPatchSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.db.models import Q


class OrdersListAPIView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = None

    def get(self, request, format=None):
        """
        Retrieves a list of orders for the current user.
        """
        if request.user.is_authenticated:
            orders = Order.objects.filter(
                Q(business_user=request.user.id) | Q(customer_user=request.user.id)
            )
        else:
            orders = Order.objects.none()

        serializer = OrdersListSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, format=None):
        """
        Creates a new order for the current user.

        This method uses the `OrdersPostSerializer` to validate the incoming
        request data. If the data is valid, it creates a new order in the database
        and returns the serialized data with an HTTP 201 status code.
        If the data is invalid, it returns the serializer errors with a 400 HTTP status code.

        :param request: The HTTP request object.
        :return: A Response object containing the serialized order data with an HTTP 201 status code
                if successful, or error details if the validation fails.
        """
        serializer = OrdersPostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(customer_user=request.user.id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SingleOrderAPIView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, pk, format=None):
        """
        Retrieves the order with the given primary key.

        This method fetches the order from the database and serializes the data
        using `OrdersListSerializer`. It then returns the serialized data with
        an HTTP 200 status code.

        :param request: The HTTP request object.
        :param pk: The primary key of the order to retrieve.
        :return: A Response object containing the serialized order data with an HTTP 200 status code.
        """
        order = Order.objects.get(pk=pk)
        serializer = OrdersListSerializer(order)
        return Response(serializer.data)

    def patch(self, request, pk, format=None):
        """
        Updates the order with the given primary key.

        This method fetches the order from the database, checks if the
        current user is allowed to update the order, and uses the
        `OrderPatchSerializer` to validate the incoming request data. If
        the data is valid, it updates the order in the database and
        returns the serialized data with an HTTP 200 status code.
        If the data is invalid, it returns the serializer errors with a
        400 HTTP status code.

        :param request: The HTTP request object.
        :param pk: The primary key of the order to update.
        :return: A Response object containing the serialized order data with an HTTP 200 status code
                if successful, or error details if the validation fails.
        """
        order = get_object_or_404(Order, pk=pk)
        is_company = order.business_user == request.user
        is_admin = request.user.is_staff
        if not (is_company or is_admin):
            return Response({"detail": ["Sie sind nicht berechtigt, diese Bestellung zu ändern."]}, status=status.HTTP_403_FORBIDDEN )
        serializer = OrderPatchSerializer(order, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            full_serializer = OrdersListSerializer(order)
            return Response(full_serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        """
        Deletes the order with the given primary key.

        This method checks if the current user is a staff user. If not, it returns a
        403 Forbidden response. Otherwise, it fetches the order from the database and
        deletes it. Finally, it returns a 204 No Content response.

        :param request: The HTTP request object.
        :param pk: The primary key of the order to delete.
        :return: A Response object with an HTTP 204 status code if successful, or
                a 403 Forbidden response if the user is not a staff user.
        """
        if not (request.user.is_staff):
            return Response(
                {"detail": ["Sie sind nicht berechtigt, diese Bestellung zu löschen."]},  status=status.HTTP_403_FORBIDDEN)
        order = get_object_or_404(Order, pk=pk)
        order.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrdersBusinessUncompletedCountAPIView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, pk, format=None):
        """
        Retrieves the count of all uncompleted orders for a business user.

        This method takes the primary key of a business user and returns the
        count of all orders of this business user that have the status "in_progress".
        If the business user does not exist, it returns a 404 Not Found response.

        :param request: The HTTP request object.
        :param pk: The primary key of the business user.
        :return: A Response object containing the count of all uncompleted
                orders of the business user with an HTTP 200 status code if
                successful, or a 404 Not Found response if the business user
                does not exist.
        """
        try:
            business_user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"detail": ["Diesen Business User gibt es nicht."]}, status=status.HTTP_404_NOT_FOUND)
        orders = Order.objects.filter(business_user=business_user, status='in_progress')
        return Response({"order_count": orders.count()})


class OrdersBusinessCompletedCountAPIView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, pk, format=None):
        """
        Retrieves the count of all completed orders for a business user.

        This method takes the primary key of a business user and returns the
        count of all orders of this business user that have the status "completed".
        If the business user does not exist, it returns a 404 Not Found response.

        :param request: The HTTP request object.
        :param pk: The primary key of the business user.
        :return: A Response object containing the count of all completed
                orders of the business user with an HTTP 200 status code if
                successful, or a 404 Not Found response if the business user
                does not exist.
        """
        try:
            business_user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"detail": ["Diesen Business User gibt es nicht."]}, status=status.HTTP_404_NOT_FOUND)
        orders = Order.objects.filter(business_user=business_user, status='completed')
        return Response({"completed_order_count": orders.count()})
