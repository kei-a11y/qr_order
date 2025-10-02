from django.urls import path
from . import views

urlpatterns = [
    # 基本画面
    path('', views.index, name='index'),
    path('initial-setup/', views.initial_setup, name='initial_setup'),
    path('logout/', views.logout, name='logout'),
    path('settings/', views.settings, name='settings'),
    
    # 管理者画面
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('menu-management/', views.menu_management, name='menu_management'),
    path('add-category/', views.add_category, name='add_category'),
    path('edit-category/<int:category_id>/', views.edit_category, name='edit_category'),
    path('delete-category/<int:category_id>/', views.delete_category, name='delete_category'),
    path('add-menu-item/', views.add_menu_item, name='add_menu_item'),
    path('edit-menu-item/<int:item_id>/', views.edit_menu_item, name='edit_menu_item'),
    path('delete-menu-item/<int:item_id>/', views.delete_menu_item, name='delete_menu_item'),
    path('table-management/', views.table_management, name='table_management'),
    path('generate-qr/<int:table_id>/', views.generate_qr_codes, name='generate_qr_codes'),
    
    # 厨房画面
    path('kitchen_view/', views.kitchen_view, name='kitchen_view'),
    path('update-order-status/<int:order_id>/', views.update_order_status, name='update_order_status'),
    
    # 顧客用画面
    path('order/<int:table_number>/', views.order_menu, name='order_menu'),
    path('submit-order/', views.submit_order, name='submit_order'),
]