from django.db import models
from django.utils import timezone

class StoreSettings(models.Model):
    """店舗設定"""
    password = models.CharField(max_length=255, help_text="ログイン用パスワード")
    wifi_ssid = models.CharField(max_length=255, help_text="WiFiのSSID", null=True, blank=True)# default='StoreWiFi', 
    wifi_password = models.CharField(max_length=255, help_text="WiFiのパスワード", null=True, blank=True)#, default='password'
    wifi_security = models.CharField(
        max_length=10,
        default='WPA',
        choices=[
            ('WPA', 'WPA/WPA2'),
            ('WEP', 'WEP'),
            ('nopass', 'なし（オープン）'),
        ],
        help_text="WiFiのセキュリティタイプ"
    )
    server_ip = models.GenericIPAddressField(help_text="サーバーのIPアドレス（注文ページ用）", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "店舗設定"
        verbose_name_plural = "店舗設定"

class Table(models.Model):
    """テーブル情報"""
    table_number = models.IntegerField(unique=True, help_text="テーブル番号")
    is_active = models.BooleanField(default=True, help_text="有効フラグ")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "テーブル"
        verbose_name_plural = "テーブル"
        ordering = ['table_number']
    
    def __str__(self):
        return f"テーブル{self.table_number}"

class MenuCategory(models.Model):
    """メニューカテゴリ"""
    name = models.CharField(max_length=100, help_text="カテゴリ名")
    order = models.IntegerField(default=0, help_text="表示順")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "メニューカテゴリ"
        verbose_name_plural = "メニューカテゴリ"
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name

class MenuItem(models.Model):
    """メニュー項目"""
    category = models.ForeignKey(MenuCategory, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=100, help_text="メニュー名")
    description = models.TextField(blank=True, help_text="説明")
    price = models.PositiveIntegerField(help_text="価格（円）")
    image = models.ImageField(upload_to='menu_images/', blank=True, null=True)
    is_available = models.BooleanField(default=True, help_text="提供可能フラグ")
    order = models.IntegerField(default=0, help_text="表示順")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "メニュー項目"
        verbose_name_plural = "メニュー項目"
        ordering = ['category__order', 'order', 'name']
    
    def __str__(self):
        return self.name

class Order(models.Model):
    """注文"""
    ORDER_STATUS_CHOICES = [
        ('pending', '受注待ち'),
        ('confirmed', '確認済み'),
        ('preparing', '調理中'),
        ('ready', '準備完了'),
        ('delivered', '提供済み'),
        ('cancelled', 'キャンセル'),
    ]
    
    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    total_amount = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True, help_text="備考")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "注文"
        verbose_name_plural = "注文"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"注文#{self.id} - テーブル{self.table.table_number}"
    
    def get_status_display_color(self):
        colors = {
            'pending': 'warning',
            'confirmed': 'info',
            'preparing': 'primary',
            'ready': 'success',
            'delivered': 'secondary',
            'cancelled': 'danger',
        }
        return colors.get(self.status, 'secondary')

class OrderItem(models.Model):
    """注文項目"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.PositiveIntegerField(help_text="注文時の単価")
    notes = models.TextField(blank=True, help_text="備考")
    
    class Meta:
        verbose_name = "注文項目"
        verbose_name_plural = "注文項目"
    
    def __str__(self):
        return f"{self.menu_item.name} x {self.quantity}"
    
    @property
    def total_price(self):
        return self.unit_price * self.quantity