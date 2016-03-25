from django.contrib import admin
from admino.sites import ModelAdmino, AdminoMixin
from models import Author, BookType, Book


class AuthorAdmin(admin.ModelAdmin):

    list_display = ("name", "creation_date")


class BookTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "creation_date")


class BookAdmin(admin.ModelAdmin):
    admin_type = "admino"
    list_display = ("name", "author")
    list_display_links = ("name", "author")

    def get_urls(self):
        return super(BookAdmin, self).get_urls()


admin.site.register(Author, AuthorAdmin)
admin.site.register(BookType, BookTypeAdmin)
admin.site.register(Book, BookAdmin)
