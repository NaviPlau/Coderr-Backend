from rest_framework import serializers
from django.urls import reverse
from offers.models import Offer, OfferDetail
from django.db import models

class OfferDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfferDetail
        fields = ['title', 'revisions', 'delivery_time_in_days', 'price', 'features', 'offer_type', 'id']
        extra_kwargs = {
            'id': {'read_only': True}
        }

    def __init__(self, *args, **kwargs):
        """
        Initializes the serializer and updates error messages for fields.

        This constructor method initializes the serializer by calling the parent
        class's initializer. It also customizes error messages for the fields
        'delivery_time_in_days', 'price', and 'revisions' to provide specific
        validation feedback in German for invalid values, minimum value requirements,
        and required field errors.
        """

        super().__init__(*args, **kwargs)
        self.fields['delivery_time_in_days'].error_messages.update({
            'invalid': "Ungültiger Wert.",
            'min_value': "Lieferzeit muss mindestens 1 Tag sein.",
            'required': "Dieses Feld ist erforderlich."
        })
        self.fields['price'].error_messages.update({
            'invalid': "Ungültiger Preis.",
            'min_value': "Preis muss höher als 1 sein.",
            'required': "Dieses Feld ist erforderlich."
        })
        self.fields['revisions'].error_messages.update({
            'invalid': "Ungültiger Wert für Revisionen.",
            'min_value': "Revisionen müssen -1 (unbegrenzt) oder eine positive Zahl sein.",
            'required': "Dieses Feld ist erforderlich."
        })

    def validate_delivery_time_in_days(self, value):
        """
        Validates the delivery time in days.

        This method checks that the provided delivery time is greater than 0.
        If the value is less than or equal to 0, it raises a ValidationError
        indicating that the delivery time must be at least one day.

        :param value: The delivery time in days to validate.
        :return: The validated delivery time in days.
        :raises ValidationError: If the delivery time is not greater than 0.
        """

        if value <= 0:
            raise serializers.ValidationError("Lieferzeit muss mindestens 1 Tag sein.")
        return value

    def validate_price(self, value):
        """
        Validates the price value.

        This method checks if the provided price is greater than 0.
        If the value is less than or equal to 0, it raises a ValidationError
        indicating that the price must be greater than 1.

        :param value: The price to validate.
        :return: The validated price.
        :raises ValidationError: If the price is not greater than 0.
        """

        if value <= 0:
            raise serializers.ValidationError("Preis muss höher als 1 sein.")
        return value

    def validate_revisions(self, value):
        """
        Validates the revisions value.

        This method checks if the provided revisions value is either -1 (indicating unlimited revisions)
        or a non-negative integer. If the value is less than -1, it raises a ValidationError
        with an appropriate error message.

        :param value: The revisions value to validate.
        :return: The validated revisions value.
        :raises ValidationError: If the revisions value is less than -1.
        """

        if value < -1:
            raise serializers.ValidationError("Revisionen müssen -1 (unbegrenzt) oder eine positive Zahl sein.")
        return value

    def validate_features(self, value):
        """
        Validates the features value.

        This method ensures that the provided features value is not empty.
        If the features value is None or has a length of zero, it raises a
        ValidationError indicating that at least one feature must be present.

        :param value: The features value to validate.
        :return: The validated features value.
        :raises ValidationError: If the features value is empty.
        """

        if not value or len(value) == 0:
            raise serializers.ValidationError("Mindestens eine Feature muss vorhanden sein.")
        return value


class OfferDetailURLSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = OfferDetail
        fields = ['id', 'url']

    def get_url(self, obj):
        return reverse('offerdetails', args=[obj.id])

class OfferSerializer(serializers.ModelSerializer):
    details = serializers.SerializerMethodField()
    min_price = serializers.SerializerMethodField()
    min_delivery_time = serializers.SerializerMethodField()
    user_details = serializers.SerializerMethodField()

    class Meta:
        model = Offer
        fields = [
            'id',
            'user',
            'title',
            'image',
            'description',
            'created_at',
            'updated_at',
            'details',
            'min_price',
            'min_delivery_time',
            'user_details'
        ]
        extra_kwargs = {
            'user': {'read_only': True} 
        }

    def to_representation(self, instance):
        """
        Customizes the representation of the serializer to remove the following fields when a POST request is made:

        - created_at
        - updated_at
        - min_price
        - min_delivery_time
        - user_details

        :param instance: The Offer instance to be serialized.
        :return: A dictionary representation of the Offer instance, with the mentioned fields removed if a POST request is made.
        """
        data = super().to_representation(instance)
        request = self.context.get('request')
        if request and request.method == 'POST':
            data.pop('created_at', None)
            data.pop('updated_at', None)
            data.pop('min_price', None)
            data.pop('min_delivery_time', None)
            data.pop('user_details', None)
            data.pop('user')
        return data
    
    def validate(self, attrs):
        """
        Validates the given data and returns the validated data if correct.
        The data to be validated must contain the key 'details' with a list of dictionaries.
        Each dictionary in the list must contain the keys 'title', 'revisions', 'delivery_time_in_days', 'price' and 'features'.
        If any of the dictionaries are not valid, it raises a serializers.ValidationError with the
        appropriate error message.
        """
        details_data = self.initial_data.get('details', [])
        errors = []
        for detail in details_data:
            detail_serializer = OfferDetailSerializer(data=detail)
            if not detail_serializer.is_valid():
                errors.append(detail_serializer.errors)

        if errors:
            raise serializers.ValidationError({"details": errors})
        attrs['validated_details'] = [
            detail_serializer.validated_data for detail_serializer in 
            map(lambda d: OfferDetailSerializer(data=d), details_data) if detail_serializer.is_valid()
        ]
        return attrs

    def get_details(self, obj):
        """
        Returns a list of OfferDetails of the given Offer instance.
        If a POST request is made, the OfferDetails are serialized using the OfferDetailSerializer.
        If not, the OfferDetails are serialized using the OfferDetailURLSerializer.
        :param obj: The Offer instance to retrieve the OfferDetails from.
        :return: A list of serialized OfferDetails.
        """
        request = self.context.get('request')
        if request and request.method == 'POST':
            return OfferDetailSerializer(obj.details.all(), many=True).data
        return OfferDetailURLSerializer(obj.details.all(), many=True).data

    def get_min_price(self, obj):
        """
        Returns the minimum price of all the OfferDetails of the given Offer instance.
        :param obj: The Offer instance to retrieve the minimum price from.
        :return: The minimum price of the OfferDetails of the given Offer instance.
        """
        return obj.details.aggregate(models.Min('price'))['price__min']

    def get_min_delivery_time(self, obj):
        """
        Returns the minimum delivery time in days of all the OfferDetails of the given Offer instance.
        :param obj: The Offer instance to retrieve the minimum delivery time from.
        :return: The minimum delivery time in days of the OfferDetails of the given Offer instance.
        """
        return obj.details.aggregate(models.Min('delivery_time_in_days'))['delivery_time_in_days__min']

    def get_user_details(self, obj):
        """
        Returns a dictionary containing the first name, last name and username of the User who created the Offer.
        :param obj: The Offer instance to retrieve the User from.
        :return: A dictionary containing the first name, last name and username of the User who created the Offer.
        """
        user = obj.user
        return {
            "first_name": user.profile.first_name,
            "last_name": user.profile.last_name,
            "username": user.profile.username
        }
    
    def create(self, validated_data):
        """
        Creates a new Offer instance with the given validated data and associated OfferDetails.

        The validated data must include a 'validated_details' key containing a list of dictionaries,
        each representing an OfferDetail to be associated with the Offer.
        
        :param validated_data: The validated data for the Offer, including 'validated_details'.
        :return: The created Offer instance.
        """

        validated_details = validated_data.pop('validated_details', [])
        offer = Offer.objects.create(**validated_data)
        for detail in validated_details:
            OfferDetail.objects.create(offer=offer, **detail)

        return offer
    
    
class SingleDetailOfOfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfferDetail
        fields = ['title', 'revisions', 'delivery_time_in_days', 'price', 'features', 'offer_type', 'id']

class SingleFullOfferDetailSerializer(serializers.ModelSerializer):
    details = SingleDetailOfOfferSerializer(many=True) 
    min_price = serializers.SerializerMethodField()
    min_delivery_time = serializers.SerializerMethodField()
    user_details = serializers.SerializerMethodField()

    class Meta:
        model = Offer
        fields = [
            'id',
            'user',
            'title',
            'image',
            'description',
            'created_at',
            'updated_at',
            'details',
            'min_price',
            'min_delivery_time',
            'user_details'
        ]

    def get_min_price(self, obj):
        """
        Returns the minimum price of all the OfferDetails of the given Offer instance.
        :param obj: The Offer instance to retrieve the minimum price from.
        :return: The minimum price of the OfferDetails of the given Offer instance.
        """
        return obj.details.aggregate(min_price=models.Min('price'))['min_price']

    def get_min_delivery_time(self, obj):
        """
        Returns the minimum delivery time of all the OfferDetails of the given Offer instance.
        :param obj: The Offer instance to retrieve the minimum delivery time from.
        :return: The minimum delivery time of the OfferDetails of the given Offer instance.
        """
        return obj.details.aggregate(min_delivery=models.Min('delivery_time_in_days'))['min_delivery']

    def get_user_details(self, obj):
        """
        Returns a dictionary containing the first name, last name and username of the User who created the Offer.
        :param obj: The Offer instance to retrieve the User from.
        :return: A dictionary containing the first name, last name and username of the User who created the Offer.
        """
        user = obj.user
        return {
            "first_name": user.profile.first_name,
            "last_name": user.profile.last_name,
            "username": user.profile.username
        }
    
    def validate(self, attrs):
        """
        Validates the incoming details data for an Offer instance.

        This method ensures that each detail in the provided details data is valid
        according to the `OfferDetailSerializer`. If any detail is invalid, it collects
        the errors and raises a `serializers.ValidationError`. If all details are valid,
        it appends the validated data to the `attrs` dictionary under the key
        'validated_details'.

        :param attrs: The attributes to be validated.
        :return: The validated attributes, including a list of validated details.
        :raises serializers.ValidationError: If any detail in the details data is invalid.
        """

        details_data = self.initial_data.get('details', [])
        errors = []
        for detail in details_data:
            detail_serializer = OfferDetailSerializer(data=detail)
            if not detail_serializer.is_valid():
                errors.append(detail_serializer.errors)
        if errors:
            raise serializers.ValidationError({"details": errors})
        attrs['validated_details'] = [
            detail_serializer.validated_data for detail_serializer in 
            map(lambda d: OfferDetailSerializer(data=d), details_data) if detail_serializer.is_valid()
        ]
        return attrs
    
    def update(self, instance, validated_data):
        """
        Updates an Offer instance with the given validated data.

        This method updates the fields of the Offer instance with the given validated
        data and saves the instance. If the validated data contains a 'details' key, it
        calls `_update_details` to update the Offer's details.

        :param instance: The Offer instance to be updated.
        :param validated_data: The validated data to update the Offer with.
        :return: The updated Offer instance.
        """
        details_data = validated_data.pop('details', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if details_data is not None:
            self._update_details(instance, details_data)
        instance.save()
        return instance

    def _update_details(self, instance, details_data):
        """
        Updates the OfferDetails associated with the given Offer instance with the given validated data.

        This method first builds a mapping of the existing OfferDetails of the Offer instance. It then
        iterates over the given validated data, and if an OfferDetail with the given id exists in the
        mapping, it calls `_update_detail_instance` to update the OfferDetail instance. If the id does
        not exist in the mapping, it creates a new OfferDetail instance with the given validated data.

        After updating and/or creating the OfferDetails, it deletes all remaining OfferDetails in the
        mapping, which are the ones that were not updated or created from the given validated data.

        :param instance: The Offer instance whose OfferDetails are to be updated.
        :param details_data: The validated data to update the OfferDetails with.
        """
        existing_details = {detail.id: detail for detail in instance.details.all()}
        for detail_data in details_data:
            detail_id = detail_data.get('id')
            if detail_id and detail_id in existing_details:
                self._update_detail_instance(existing_details.pop(detail_id), detail_data)
            else:
                OfferDetail.objects.create(offer=instance, **detail_data)
        for remaining_detail in existing_details.values():
            remaining_detail.delete()

    def _update_detail_instance(self, detail_instance, detail_data):
        """
        Updates the given OfferDetail instance with the given validated data.

        This method sets the given validated data as attributes of the given OfferDetail instance and saves it.

        :param detail_instance: The OfferDetail instance to be updated.
        :param detail_data: The validated data to update the OfferDetail with.
        """
        for attr, value in detail_data.items():
            setattr(detail_instance, attr, value)
        detail_instance.save()
      
