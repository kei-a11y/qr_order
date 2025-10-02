from django.contrib import admin
from .models import StoreSettings, Table, MenuCategory, MenuItem, Order, OrderItem

@admin.register(StoreSettings)
class StoreSettingsAdmin(admin.ModelAdmin):
    list_display = ['id', 'wifi_ssid', 'server_ip', 'wifi_security', 'created_at', 'updated_at']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ['table_number', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['table_number']

@admin.register(MenuCategory)
class MenuCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']
    ordering = ['order', 'name']

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['total_price']

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'is_available', 'order', 'created_at']
    list_filter = ['category', 'is_available', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['category__order', 'order', 'name']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'table', 'status', 'total_amount', 'created_at']
    list_filter = ['status', 'created_at', 'table']
    search_fields = ['id', 'table__table_number', 'notes']
    ordering = ['-created_at']
    inlines = [OrderItemInline]
    readonly_fields = ['created_at', 'updated_at']

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'menu_item', 'quantity', 'unit_price', 'total_price']
    list_filter = ['order__created_at', 'menu_item__category']
    search_fields = ['order__id', 'menu_item__name']