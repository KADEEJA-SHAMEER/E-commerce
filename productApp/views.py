from django.shortcuts import render
from rest_framework.decorators import api_view,permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import *
from .serializers import *
from django.shortcuts import get_object_or_404
from django.db import transaction
import razorpay
# Create your views here.

@api_view(['GET'])
def product_list(request):
    products=Product.objects.all()
    serializer=ProductSerializer(products,many=True)
    return Response(serializer.data)


@api_view(['GET'])
def product_detail(request,pk):
    try:
        product=Product.objects.get(id=pk)
    except Product.DoesNotExists:
        return Response({"errors":"product not found"},status=404)
    serializer=ProductSerializer(product)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_to_cart(request):
    product_id = request.data.get('product_id')
    quantity = request.data.get('quantity', 1)  

    if not product_id:
        return Response({"error": "product_id is required"}, status=400)

    try:
        quantity = int(quantity)
        if quantity < 1:
            raise ValueError
    except ValueError:
        return Response({"error": "quantity must be a positive number"}, status=400)

    product = get_object_or_404(Product, id=product_id)

    cart_item, created = Cart.objects.get_or_create(
        user=request.user,
        product=product
    )

    if created:
        cart_item.quantity = quantity
    else:
        cart_item.quantity += quantity

    cart_item.save()

    return Response({
        "message": "Product added to cart",
        "product": product.name,
        "quantity": cart_item.quantity
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def view_cart(request):
    cart_items = Cart.objects.filter(user=request.user)

    data = []
    total_price = 0

    for item in cart_items:
        item_total = item.product.price * item.quantity
        total_price += item_total

        data.append({
            "cart_id": item.id,
            "product_id": item.product.id,
            "product_name": item.product.name,
            "price": float(item.product.price),
            "quantity": item.quantity,
            "item_total": float(item_total)
        })

    return Response({
        "items": data,
        "total_price": float(total_price)
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def remove_from_cart(request):
    product_id = request.data.get('product_id')

    if not product_id:
        return Response({"error": "product_id is required"}, status=400)

    Cart.objects.filter(
        user=request.user,
        product_id=product_id
    ).delete()

    return Response({"message": "Product removed from cart"})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def checkout(request):
    user = request.user
    cart_items = Cart.objects.filter(user=user)

    if not cart_items.exists():
        return Response({"message": "Cart is empty"}, status=400)

    total_amount = 0
    for item in cart_items:
        total_amount += item.product.price * item.quantity

    # Razorpay expects amount in paise
    razorpay_amount = int(total_amount * 100)

    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )

    razorpay_order = client.order.create({
        "amount": razorpay_amount,
        "currency": "INR",
        "payment_capture": 1
    })

    with transaction.atomic():
        order = Order.objects.create(
            user=user,
            total_amount=total_amount,
            razorpay_order_id=razorpay_order["id"]
        )

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )

        cart_items.delete()

    return Response({
        "message": "Order created",
        "order_id": order.id,
        "razorpay_order_id": razorpay_order["id"],
        "amount": razorpay_amount,
        "razorpay_key": settings.RAZORPAY_KEY_ID
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def buy_now_checkout(request):
    user = request.user

    product_id = request.data.get('product_id')
    quantity = int(request.data.get('quantity', 1))

    if not product_id:
        return Response({"error": "product_id is required"}, status=400)

    product = get_object_or_404(Product, id=product_id)

    total_amount = product.price * quantity
    razorpay_amount = int(total_amount * 100)

    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )

    razorpay_order = client.order.create({
        "amount": razorpay_amount,
        "currency": "INR",
        "payment_capture": 1
    })

    with transaction.atomic():
        order = Order.objects.create(
            user=user,
            total_amount=total_amount,
            razorpay_order_id=razorpay_order["id"]
        )

        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=quantity,
            price=product.price
        )

    return Response({
        "message": "Buy now order created",
        "order_id": order.id,
        "razorpay_order_id": razorpay_order["id"],
        "amount": razorpay_amount,
        "razorpay_key": settings.RAZORPAY_KEY_ID
    })
