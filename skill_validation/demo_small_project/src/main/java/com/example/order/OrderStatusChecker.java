package com.example.order;

public class OrderStatusChecker {
    public boolean isPaid(Order order) {
        return order.getStatus().equals("PAID");
    }
}
