
# RFM İLE MUSTERİ SEGMENTASYONU
import pandas as pd
import datetime as dt

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.float_format', lambda x: '%.5f' % x)


############################
# Veri Seti Hikayesi
############################
# Online Retail II isimli veri seti İngiltere merkezli online bir satış mağazasının 01/12/2009 - 09/12/2011 tarihleri arasındaki satışlarını içermektedir.
# Bu şirketin ürün kataloğunda hediyelik eşyalar yer almaktadır. 
# Şirketin müşterilerinin büyük çoğunluğu kurumsal müşterilerdir.


#########################
#Değişkenler
#########################

# InvoiceNo – Fatura Numarası
# Eğer bu kod C ile başlıyorsa işlemin iptal edildiğini ifade eder.
# StockCode – Ürün kodu Her bir ürün için eşsiz numara.
# Description – Ürün ismi Quantity – Ürün adedi
# Faturalardaki ürünlerden kaçar tane satıldığını ifade etmektedir.
# InvoiceDate – Fatura tarihi UnitPrice – Fatura fiyatı (Sterlin)
# CustomerID – Eşsiz müşteri numarası Country – Ülke ismi


################################
# VERİYİ ANLAMA VE HAZIRLAMA
#################################
# Veri setini okuma
df_ = pd.read_excel("online_retail_II.xlsx", sheet_name="Year 2010-2011")

# df kopyası olusturma
df = df_.copy()

#sayısal degiskenlerin özet istatistikleri
df.describe().T


df.head()

# eksik degerler var mı? kac tane?
df.isnull().sum()

# eksik degerleri silelim.
df.dropna(inplace=True)
df.isnull().sum()

# essiz urun sayisi nedir?
df["Description"].nunique()

# hangi urunden kacar tane var?
df["Description"].value_counts().head()

# en cok siparis edilen urun hangisi?
df.groupby("Description").agg({"Quantity": "sum"}).head()

# iade olan ürünleri de dısarda bırakalım
df = df[~df["Invoice"].str.contains("C", na=False)]
df.head()


# quantity ve price 0'dan büyük olmalıdır. bunu belirtiyoruz.
df = df[(df['Quantity'] > 0)]
df = df[(df['Price'] > 0)]

# toplam fiyat degeri hesaplanır.
df["TotalPrice"] = df["Quantity"] * df["Price"]


df.head()

###########################################
# RFM METRİKLERİNİN HESAPLANMASI
############################################

# veri setinde en son fatura kesilen tarihe bakalım
df["InvoiceDate"].max()

#bugunün tarihi
today_date = dt.datetime(2011, 12, 11)

#müşteri özelinde metrikleri hesaplama
rfm = df.groupby('Customer ID').agg({'InvoiceDate': lambda InvoiceDate: (today_date - InvoiceDate.max()).days,
                                     'Invoice': lambda Invoice: Invoice.nunique(),
                                     'TotalPrice': lambda TotalPrice: TotalPrice.sum()})


# metrikleri rfm'e atayınız.
rfm.columns = ['recency', 'frequency', 'monetary']

rfm.head()

#################################
# RFM Skorlarının Oluşturulması
#################################

# recency frequency ve monetary metriklerinin skorlara dönüştürülmesi.

# Recency score;
# en son tarih skoru. Burada 1 en yakın, 5 en uzak tarih olmaktadır.
# Bizim için en önemli durum en yakın tarih 1 olduğu için 1 5'ten daha yüksek öneme sahiptir.
rfm["recency_score"] = pd.qcut(rfm['recency'], 5, labels=[5, 4, 3, 2, 1])

# Frequency score:
# alısveriş sıklıgı skorudur.
# burada 1 en az sıklıgı, 5 en fazla sıklıgı temsil eder.
rfm["frequency_score"] = pd.qcut(rfm['frequency'].rank(method="first"), 5, labels=[1, 2, 3, 4, 5])

# Monetary score:
rfm["monetary_score"] = pd.qcut(rfm['monetary'], 5, labels=[1, 2, 3, 4, 5])

#olusan iki farklı degişkenin degerini tek bir degişken olarak ifade edelim
rfm["RFM_SCORE"] = (rfm['recency_score'].astype(str) + rfm['frequency_score'].astype(str))


rfm.head()

##########################################
# RFM skorların segment olarak tanımlanması
##########################################

seg_map = {
    r'[1-2][1-2]': 'hibernating',
    r'[1-2][3-4]': 'at_Risk',
    r'[1-2]5': 'cant_loose',
    r'3[1-2]': 'about_to_sleep',
    r'33': 'need_attention',
    r'[3-4][4-5]': 'loyal_customers',
    r'41': 'promising',
    r'51': 'new_customers',
    r'[4-5][2-3]': 'potential_loyalists',
    r'5[4-5]': 'champions'
}

# segment degişkeni ekliyoruz. score degerlerini kullan ama replace metodu ile yerine karsılık gelen segmentleri yaz.
# birleştirilen skorlar seg_map ile değiştirildi
rfm['segment'] = rfm['RFM_SCORE'].replace(seg_map, regex=True)

rfm.head()


##################################
# Secilen Segmentleri Yorumlayalım
####################################

# segment'lere göre recency frequency ve monetary degerleri gruplayarak ortalama degerlerine bakalım.
rfm[["segment", "recency", "frequency", "monetary"]].groupby("segment").agg(["mean", "count"])

# loyal customers segmentindeki müşteriler
rfm[rfm["segment"] == "loyal_customers"].head()


new_df = pd.DataFrame()
# boş bir df olusturduk.


# local customer segmentinin indexleri yeni değişkene atanır.
new_df["local_customer_id"] = rfm[rfm["segment"] == "loyal_customers"].index
new_df.head()

new_df.to_csv("local_customers.csv")  # df'i csv dosyası olarak kaydet


#cant_loose:  bana göre önem sırasında ilk üçte yer alabilecek segmenttir.
#             elde olan müşteriyi tutmak, yeni müşteri kazanmaktan daha az maliyetlidir.
#             zamanında sıklıkla alısveriş yapmıs fakat son zamanlarda uzaklasmıs olan bu segmente hatırlatıcı kampanyalar düzenlenebilir.

#new_customers:  bu segmentteki müşterilere iyi izlenim bırakılabilirse champion veya sadık müşteri segmentine taşıyabiliriz
#                bu sebeple, kendilerine özel ilgi gösterildigini düşündüren kampanyalar düzenlenebilir.



