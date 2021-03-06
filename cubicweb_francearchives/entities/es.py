# -*- coding: utf-8 -*-
#
# Copyright © LOGILAB S.A. (Paris, FRANCE) 2016-2019
# Contact http://www.logilab.fr -- mailto:contact@logilab.fr
#
# This software is governed by the CeCILL-C license under French law and
# abiding by the rules of distribution of free software. You can use,
# modify and/ or redistribute the software under the terms of the CeCILL-C
# license as circulated by CEA, CNRS and INRIA at the following URL
# "http://www.cecill.info".
#
# As a counterpart to the access to the source code and rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty and the software's author, the holder of the
# economic rights, and the successive licensors have only limited liability.
#
# In this respect, the user's attention is drawn to the risks associated
# with loading, using, modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean that it is complicated to manipulate, and that also
# therefore means that it is reserved for developers and experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systemsand/or
# data to be ensured and, more generally, to use and operate it in the
# same conditions as regards security.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL-C license and that you accept its terms.
#

"""elasticsearch customization"""


from cubicweb.predicates import is_instance
from cubicweb.view import EntityAdapter

from cubicweb_elasticsearch import es
from cubicweb_elasticsearch.entities import Indexer
from cubicweb_elasticsearch.entities import IFullTextIndexSerializable


from cubicweb_francearchives.utils import remove_html_tags

SUGGEST_ETYPES = ("AgentAuthority", "LocationAuthority", "SubjectAuthority")
ALL_INDEXABLE_ETYPES = []


class PniaIndexer(Indexer):
    analyser_settings = {
        "analysis": {
            "filter": {
                "elision": {
                    "type": "elision",
                    "articles": ["l", "m", "t", "qu", "n", "s", "j", "d"],
                },
                "my_ascii_folding": {
                    "type": "asciifolding",
                    "preserve_original": True,
                },
            },
            "analyzer": {
                "default": {
                    "filter": ["my_ascii_folding", "lowercase", "elision"],
                    "tokenizer": "standard",
                }
            },
        }
    }

    # TODO - inspect which fields are used in facets to generate not_analyzed
    @property
    def mapping(self):
        mapping = {
            "dynamic_templates": [
                {
                    "concat_all_texts": {
                        "match_mapping_type": "string",
                        "unmatch": "alltext",
                        "mapping": {"type": "text", "copy_to": "alltext"},
                    }
                }
            ],
            "properties": {
                # implement implicity type behaviour of ES 2.x with
                # an explicit "estype" field
                "estype": {"type": "keyword"},
                # all types
                "cw_etype": {"type": "keyword"},
                "index_entries": {
                    "type": "nested",
                    "include_in_parent": True,
                    "properties": {
                        "label": {"type": "keyword", "copy_to": ["alltext"]},
                        "normalized": {"type": "keyword"},
                        "type": {"type": "keyword"},
                    },
                },
                "title_en": {"type": "text", "copy_to": "alltext_en", "analyzer": "english"},
                "title_es": {"type": "text", "copy_to": "alltext_en", "analyzer": "spanish"},
                "title_de": {"type": "text", "copy_to": "alltext_en", "analyzer": "german"},
                "subtitle_en": {"type": "text", "copy_to": "alltext_en", "analyzer": "english"},
                "subtitle_es": {"type": "text", "copy_to": "alltext_en", "analyzer": "spanish"},
                "subtitle_de": {"type": "text", "copy_to": "alltext_en", "analyzer": "german"},
                "content_en": {"type": "text", "copy_to": "alltext_en", "analyzer": "english"},
                "content_es": {"type": "text", "copy_to": "alltext_en", "analyzer": "spanish"},
                "content_de": {"type": "text", "copy_to": "alltext_en", "analyzer": "german"},
                "short_description_en": {
                    "type": "text",
                    "copy_to": "alltext_en",
                    "analyzer": "english",
                },
                "short_description_es": {
                    "type": "text",
                    "copy_to": "alltext_en",
                    "analyzer": "spanish",
                },
                "short_description_de": {
                    "type": "text",
                    "copy_to": "alltext_en",
                    "analyzer": "german",
                },
                "alltext": {"type": "text"},
                "alltext_en": {"type": "text", "analyzer": "english"},
                "alltext_de": {"type": "text", "analyzer": "spanish"},
                "alltext_es": {"type": "text", "analyzer": "german"},
                "escategory": {"type": "keyword"},
                # FindingAid, FAComponent
                "originators": {"type": "keyword", "copy_to": "alltext"},
                # FindingAid, FAComponent, ExternRef, BaseContent
                "publisher": {"type": "keyword", "copy_to": "alltext"},
                # Circular
                "status": {"type": "keyword", "copy_to": "alltext"},
                "business_field": {"type": "keyword", "copy_to": "alltext"},
                "archival_field": {"type": "keyword", "copy_to": "alltext"},
                "document_type": {"type": "keyword", "copy_to": "alltext"},
                "historical_context": {"type": "keyword", "copy_to": "alltext"},
                "action": {"type": "keyword", "copy_to": "alltext"},
                "occupation": {"type": "keyword", "copy_to": "alltext"},
                "function": {"type": "keyword", "copy_to": "alltext"},
                "genreform": {"type": "keyword", "copy_to": "alltext"},
                # Service
                "level": {"type": "keyword"},
                "sort_name": {"type": "keyword"},
                # ExternRef
                "reftype": {"type": "keyword"},
                "in_state": {"type": "keyword"},
                "creation_date": {"type": "date"},
                # FindingAid, FAComponent
                "dates": {"type": "integer_range"},
                "startyear": {"type": "date", "format": "yyyy"},
                "stopyear": {"type": "date", "format": "yyyy"},
                "sortdate": {"type": "date", "format": "yyyy-MM-dd"},
                "service": {
                    "properties": {
                        "eid": {"type": "integer"},
                        "code": {"type": "keyword"},
                        "level": {"type": "keyword"},
                        "title": {"type": "keyword"},
                    }
                },
                "digitized_versions": {
                    "properties": {
                        "url": {"type": "keyword"},
                        "role": {"type": "keyword"},
                        "illustration_url": {"type": "keyword"},
                    }
                },
            },
        }
        return mapping

    @property
    def index_name(self):
        return "%s_all" % self._cw.vreg.config["index-name"]

    @property
    def settings(self):
        settings = Indexer.settings.copy()
        settings.update(
            {
                "settings": self.analyser_settings,
                "mappings": self.mapping,
            }
        )
        return settings


class PniaSuggestIndexer(Indexer):
    """indexer for autocomplete search"""

    __regid__ = "suggest-indexer"
    adapter = "ISuggestIndexSerializable"

    indexable_etypes = SUGGEST_ETYPES
    analyser_settings = {
        "analysis": {
            "filter": {
                "ngram_filter": {"type": "edgeNGram", "min_gram": 1, "max_gram": 20},
                "my_ascii_folding": {"preserve_original": True, "type": "asciifolding"},
                "french_snowball": {"type": "snowball", "language": "French"},
            },
            "analyzer": {
                "search_analyzer": {
                    "tokenizer": "standard",
                    "filter": ["lowercase", "asciifolding"],
                },
                "autocomplete": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "my_ascii_folding", "ngram_filter"],
                },
            },
        },
    }

    mapping_properties = {
        "properties": {
            "text": {
                "search_analyzer": "search_analyzer",
                "analyzer": "autocomplete",
                "type": "text",
            }
        }
    }

    @property
    def index_name(self):
        return "{}_suggest".format(self._cw.vreg.config["index-name"])

    @property
    def settings(self):
        return {"mappings": self.mapping_properties.copy(), "settings": self.analyser_settings}


class PniaIFullTextIndexSerializable(IFullTextIndexSerializable):
    def process_attributes(self):
        data = {}
        eschema = self.entity.e_schema
        for attr in self.fulltext_indexable_attributes:
            value = getattr(self.entity, attr)
            if value and eschema.has_metadata(attr, "format"):
                value = remove_html_tags(value)
            data[attr] = value
        data["estype"] = self.entity.cw_etype
        return data


class TranslatableIndexSerializableMixin(object):
    def add_translations(self, complete=True, **kwargs):
        data = {}
        translations = self.entity.reverse_translation_of
        if not translations:
            return data
        eschema = translations[0].e_schema
        indexables = [attr.type for attr in eschema.indexable_attributes()]
        for lang, values in self.entity.translations(**kwargs).items():
            for attribute, value in values.items():
                if attribute not in indexables:
                    continue
                if value and eschema.has_metadata(attribute, "format"):
                    value = remove_html_tags(value)
                data["{attr}_{lang}".format(attr=attribute, lang=lang)] = value
        return data


class ISuggestIndexSerializable(EntityAdapter):
    __regid__ = "ISuggestIndexSerializable"
    __select__ = is_instance(*SUGGEST_ETYPES)
    etype2type = {
        "LocationAuthority": "geogname",
        "SubjectAuthority": "subject",
        "AgentAuthority": "agent",
    }
    etype2urlsegment = {
        "LocationAuthority": "location",
        "SubjectAuthority": "subject",
        "AgentAuthority": "agent",
    }

    @property
    def es_id(self):
        return self.entity.eid

    @property
    def es_doc_type(self):
        return "_doc"

    def related_docs_queries(self, published=False):
        """Get queries to compute the number of related
        documents.

        :param bool published: whether published documents should be included

        :returns: list of queries
        :rtype: list
        """
        if published:
            state = ", F in_state S, S name '{}'".format("wfs_cmsobject_published")
        else:
            state = ""
        queries = [
            """(DISTINCT Any F WHERE EXISTS(A authority X, A index F),
            X eid %(eid)s, F is FindingAid{state})""",
            """(DISTINCT Any FA WHERE EXISTS(A authority X, A index FA, X eid %(eid)s),
            FA finding_aid F{state})""",
            """(DISTINCT Any F WHERE EXISTS(F? related_authority X),
            X eid %(eid)s{state})""",
        ]
        if self.entity.cw_etype == "SubjectAuthority":
            queries.append(
                """(DISTINCT Any F WHERE
                              EXISTS (F business_field B, X same_as B)
                              OR EXISTS(F historical_context H, X same_as H)
                              OR EXISTS(F document_type D, X same_as D)
                              OR EXISTS(F action A, X same_as A),
                              X eid %(eid)s{state})"""
            )
        return [query.format(state=state) for query in queries]

    def published_docs(self):
        """compute the number of related published :
        - FindingAids
        - FAComponents
        - Circulars
        - Entities related by `related_authority` relation
        """
        return self._cw.execute(
            """Any COUNT(F) WITH F BEING ({queries})""".format(
                queries=" UNION ".join(self.related_docs_queries(published=True))
            ),
            {"eid": self.entity.eid},
        )[0][0]

    def all_docs(self):
        """compute the number of all related :
        - FindingAids
        - FAComponents
        - Circulars
        - Entities related by `related_authority`
        """
        return self._cw.execute(
            """Any COUNT(F) WITH F BEING ({queries})""".format(
                queries=" UNION ".join(self.related_docs_queries())
            ),
            {"eid": self.entity.eid},
        )[0][0]

    def grouped(self):
        query = """
            Any COUNT(X1) WHERE X eid {eid}, X grouped_with X1?"""
        return bool(self._cw.execute(query.format(eid=self.entity.eid))[0][0])

    def related_docs(self, published=False):
        """compute the number of related FindingAids and FAComponents:
        - total number if published == False
        - number of published entities if published == True
        flag groupped auhtorities"""
        if published:
            docs = self.published_docs()
        else:
            docs = self.all_docs()
        return docs

    def serialize(self, complete=True, published=False):
        entity = self.entity
        if complete:
            entity.complete()
        etype = entity.cw_etype
        return {
            "cw_etype": etype,
            "eid": entity.eid,
            "text": entity.label,
            # do not use type from Geogname, Subject, AgentName
            # because user could have group authorities so
            # one authority could have 2 AgentName with two different
            # type
            "type": self.etype2type[etype],
            "additional": "",
            "urlpath": "{}/{}".format(self.etype2urlsegment[etype], entity.eid),
            "count": self.related_docs(published=published),
            "grouped": self.grouped(),
        }


def registration_callback(vreg):
    global ALL_INDEXABLE_ETYPES
    vreg.register_all(list(globals().values()), __name__)
    vreg.unregister(Indexer)
    vreg.unregister(IFullTextIndexSerializable)
    ALL_INDEXABLE_ETYPES = es.indexable_types(vreg.schema) + ["FindingAid", "FAComponent"]
