import json
import logging
from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_scan

from app.config import Config

logger = logging.getLogger('dug')


class SearchException(Exception):
    def __init__(self, message, details):
        self.message = message
        self.details = details


class Search:
    """ Search -
    1. Lexical fuzziness; (a) misspellings - a function of elastic.
    2. Fuzzy ontologically;
       (a) expand based on core queries
         * phenotype->study
         * phenotype->disease->study
         * disease->study
         * disease->phenotype->study
    """

    def __init__(self, cfg: Config, indices=None):

        if indices is None:
            indices = ['concepts_index', 'variables_index', 'kg_index']

        self._cfg = cfg
        logger.debug(
            f"Connecting to elasticsearch host: {self._cfg.elastic_host} at port: {self._cfg.elastic_port}")

        self.indices = indices

        self.hosts = [{'host': self._cfg.elastic_host,
                       'port': self._cfg.elastic_port, 'scheme': self._cfg.elastic_scheme}]

        logger.debug(
            f"Authenticating as user {self._cfg.elastic_username} to host:{self.hosts}")

        self.es = AsyncElasticsearch(hosts=self.hosts,
                                     http_auth=(self._cfg.elastic_username, self._cfg.elastic_password))

    async def dump_concepts(self, index, query={}, size=None, fuzziness=1, prefix_length=3):
        """
        Get everything from concept index
        """
        query = {
            "match_all": {}
        }
        body = {"query": query}
        await self.es.ping()
        total_items = await self.es.count(body=body, index=index)
        counter = 0
        all_docs = []
        async for doc in async_scan(
            client=self.es,
            query=body,
            index=index
        ):
            if counter == size and size != 0:
                break
            counter += 1
            all_docs.append(doc)
        return {
            "status": "success",
            "result": {
                "hits": {
                    "hits": all_docs
                },
                "total_items": total_items
            },
            "message": "Search result"
        }

    async def agg_data_type(self):
        aggs = {
            "data_type": {
                "terms": {
                    "field": "data_type.keyword",
                }
            }
        }

        body = {'aggs': aggs}
        results = await self.es.search(
            index="variables_index",
            body=body
        )
        data_type_list = [data_type['key']
                          for data_type in results['aggregations']['data_type']['buckets']]
        results.update({'data type list': data_type_list})
        return data_type_list

    async def search_concepts(self, query, offset=0, size=None, fuzziness=1, prefix_length=3):
        """
        Changed to a long boolean match query to optimize search results
        """
        query = {
            "bool": {
                "should": [
                    {
                        "match_phrase": {
                            "name": {
                                "query": query,
                                "boost": 10
                            }
                        }
                    },
                    {
                        "match_phrase": {
                            "description": {
                                "query": query,
                                "boost": 6
                            }
                        }
                    },
                    {
                        "match_phrase": {
                            "search_terms": {
                                "query": query,
                                "boost": 8
                            }
                        }
                    },
                    {
                        "match": {
                            "name": {
                                "query": query,
                                "fuzziness": fuzziness,
                                "prefix_length": prefix_length,
                                "operator": "and",
                                "boost": 4
                            }
                        }
                    },
                    {
                        "match": {
                            "search_terms": {
                                "query": query,
                                "fuzziness": fuzziness,
                                "prefix_length": prefix_length,
                                "operator": "and",
                                "boost": 5
                            }
                        }
                    },
                    {
                        "match": {
                            "description": {
                                "query": query,
                                "fuzziness": fuzziness,
                                "prefix_length": prefix_length,
                                "operator": "and",
                                "boost": 3
                            }
                        }
                    },
                    {
                        "match": {
                            "description": {
                                "query": query,
                                "fuzziness": fuzziness,
                                "prefix_length": prefix_length,
                                "boost": 2
                            }
                        }
                    },
                    {
                        "match": {
                            "search_terms": {
                                "query": query,
                                "fuzziness": fuzziness,
                                "prefix_length": prefix_length,
                                "boost": 1
                            }
                        }
                    },
                    {
                        "match": {
                            "optional_terms": {
                                "query": query,
                                "fuzziness": fuzziness,
                                "prefix_length": prefix_length
                            }
                        }
                    }
                ]
            }
        }
        body = {'query': query}
        total_items = await self.es.count(body=body, index="concepts_index")
        search_results = await self.es.search(
            index="concepts_index",
            body=body,
            filter_path=['hits.hits._id', 'hits.hits._type',
                         'hits.hits._source', 'hits.hits._score'],
            from_=offset,
            size=size
        )
        search_results.update({'total_items': total_items['count']})
        return search_results

    async def search_variables(self, concept="", query="", size=None, data_type=None, offset=0, fuzziness=1,
                               prefix_length=3):
        """
        In variable seach, the concept MUST match one of the indentifiers in the list
        The query can match search_terms (hence, "should") for ranking.
        Results Return
        The search result is returned in JSON format {collection_id:[elements]}
        Filter
        If a data_type is passed in, the result will be filtered to only contain
        the passed-in data type.
        """
        query = {
            'bool': {
                'should': {
                    "match": {
                        "identifiers": concept
                    }
                },
                'should': [
                    {
                        "match_phrase": {
                            "element_name": {
                                "query": query,
                                "boost": 10
                            }
                        }
                    },
                    {
                        "match_phrase": {
                            "element_desc": {
                                "query": query,
                                "boost": 6
                            }
                        }
                    },
                    {
                        "match_phrase": {
                            "search_terms": {
                                "query": query,
                                "boost": 8
                            }
                        }
                    },
                    {
                        "match": {
                            "element_name": {
                                "query": query,
                                "fuzziness": fuzziness,
                                "prefix_length": prefix_length,
                                "operator": "and",
                                "boost": 4
                            }
                        }
                    },
                    {
                        "match": {
                            "search_terms": {
                                "query": query,
                                "fuzziness": fuzziness,
                                "prefix_length": prefix_length,
                                "operator": "and",
                                "boost": 5
                            }
                        }
                    },
                    {
                        "match": {
                            "element_desc": {
                                "query": query,
                                "fuzziness": fuzziness,
                                "prefix_length": prefix_length,
                                "operator": "and",
                                "boost": 3
                            }
                        }
                    },
                    {
                        "match": {
                            "element_desc": {
                                "query": query,
                                "fuzziness": fuzziness,
                                "prefix_length": prefix_length,
                                "boost": 2
                            }
                        }
                    },
                    {
                        "match": {
                            "element_name": {
                                "query": query,
                                "fuzziness": fuzziness,
                                "prefix_length": prefix_length,
                                "boost": 2
                            }
                        }
                    },
                    {
                        "match": {
                            "search_terms": {
                                "query": query,
                                "fuzziness": fuzziness,
                                "prefix_length": prefix_length,
                                "boost": 1
                            }
                        }
                    },
                    {
                        "match": {
                            "optional_terms": {
                                "query": query,
                                "fuzziness": fuzziness,
                                "prefix_length": prefix_length
                            }
                        }
                    }
                ]
            }
        }

        if concept:
            query['bool']['must'] = {
                "match": {
                    "identifiers": concept
                }
            }

        body = {'query': query}
        total_items = await self.es.count(body=body, index="variables_index")
        search_results = await self.es.search(
            index="variables_index",
            body=body,
            filter_path=['hits.hits._id', 'hits.hits._type',
                         'hits.hits._source', 'hits.hits._score'],
            from_=offset,
            size=size
        )

        # Reformat Results
        new_results = {}
        if not search_results:
           # we don't want to error on a search not found
           new_results.update({'total_items': total_items['count']})
           return new_results

        for elem in search_results['hits']['hits']:
            elem_s = elem['_source']
            elem_type = elem_s['data_type']
            if elem_type not in new_results:
                new_results[elem_type] = {}

            elem_id = elem_s['element_id']
            coll_id = elem_s['collection_id']
            elem_info = {
                "description": elem_s['element_desc'],
                "e_link": elem_s['element_action'],
                "id": elem_id,
                "name": elem_s['element_name'],
                "score": round(elem['_score'], 6)
            }

            # Case: collection not in dictionary for given data_type
            if coll_id not in new_results[elem_type]:
                # initialize document
                doc = {}

                # add information
                doc['c_id'] = coll_id
                doc['c_link'] = elem_s['collection_action']
                doc['c_name'] = elem_s['collection_name']
                doc['elements'] = [elem_info]

                # save document
                new_results[elem_type][coll_id] = doc

            # Case: collection already in dictionary for given element_type; append elem_info.  Assumes no duplicate elements
            else:
                new_results[elem_type][coll_id]['elements'].append(elem_info)

        # Flatten dicts to list
        for i in new_results:
            new_results[i] = list(new_results[i].values())

        # Return results
        if bool(data_type):
            if data_type in new_results:
                new_results = new_results[data_type]
            else:
                new_results = {}
        return new_results

    async def search_kg(self, unique_id, query, offset=0, size=None, fuzziness=1, prefix_length=3):
        """
        In knowledge graph search the concept MUST match the unique ID
        The query MUST match search_targets.  The updated query allows for
        fuzzy matching and for the default OR behavior for the query.
        """
        query = {
            "bool": {
                "must": [
                    {"term": {
                        "concept_id.keyword": unique_id
                    }
                    },
                    {'query_string': {
                        "query": query,
                        "fuzziness": fuzziness,
                        "fuzzy_prefix_length": prefix_length,
                        "default_field": "search_targets"
                    }
                    }
                ]
            }
        }
        body = {'query': query}
        total_items = await self.es.count(body=body, index="kg_index")
        search_results = await self.es.search(
            index="kg_index",
            body=body,
            filter_path=['hits.hits._id',
                         'hits.hits._type', 'hits.hits._source'],
            from_=offset,
            size=size
        )
        search_results.update({'total_items': total_items['count']})
        return search_results
