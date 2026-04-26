from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    """Sitemap for all static (non-dynamic) pages of BMPPD."""

    protocol = "https"
    changefreq = "monthly"
    priority = 0.8

    def items(self):
        return [
            "bmppd",
            "about",
            "acknowledgement",
        ]

    def location(self, item):
        return reverse(item)

    def priority(self, item):
        priorities = {
            "bmppd": 1.0,        # Home / search — highest priority
            "about": 0.6,
            "acknowledgement": 0.5,
        }
        return priorities.get(item, 0.5)
