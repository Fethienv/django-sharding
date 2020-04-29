
import copy
import warnings

from itertools import islice, chain

from django.db import DJANGO_VERSION_PICKLE_KEY
from django.db.models import sql
from django.db.models.query import EmptyQuerySet, QuerySet
from django.db.models.query_utils import Q
from django.utils.version import get_version
from django.core.exceptions import (FieldError, MultipleObjectsReturned,
                                    ObjectDoesNotExist)

from sharding.querysetsequence import QuerySetSequence

from .models import Databases

REPR_OUTPUT_SIZE = 21

class MultiDBQuerySet:

    def __init__(self, model=None, db_list=None, multidbquerysets=None, filter_args=(), filter_kwargs={}, **kwargs):

        self.model     = model
        self._db_list  = db_list
        self.multidbquerysets = []
        self.query     = sql.Query(self.model)
        self.__multidbquerysets = multidbquerysets
        self.index = 0

        self.filter_args   = filter_args
        self.filter_kwargs = filter_kwargs

        self._set_multidbquerysets()

    def as_manager(cls):# to refverify
        # Address the circular dependency between `Queryset` and `Manager`.
        from django.db.models.manager import Manager
        manager = Manager.from_queryset(cls)()
        manager._built_with_as_manager = True
        return manager
    as_manager.queryset_only = True
    as_manager = classmethod(as_manager)

    ########################
    # PYTHON MAGIC METHODS #
    ########################

    def __iter__(self):
        return iter(self._chain())
    
    def __next__(self):
        if self.index > len(self.multidbquerysets):
            raise StopIteration
        multidbquerysets = list(self._chain())[self.index]
        self.index += 1
        return multidbquerysets

    def __repr__(self):
        data = list(self[:REPR_OUTPUT_SIZE + 1])
        if len(data) > REPR_OUTPUT_SIZE:
            data[-1] = "...(remaining elements truncated)..."
        return '<%s %r>' % (self.__class__.__name__, data)

    def __getitem__(self, k):
        return self._chain()

    def __len__(self):
        return len(list(self.multidbquerysets))

    def __deepcopy__(self, memo): # same in QuerySet 
        """Don't populate the MultiDBQuerySet's cache."""
        obj = self.__class__()
        for k, v in self.__dict__.items():
            if k == '_result_cache':
                obj.__dict__[k] = None
            else:
                obj.__dict__[k] = copy.deepcopy(v, memo)
        return obj

    def __getstate__(self): # same in QuerySet
        self._set_multidbquerysets()
        return {**self.__dict__, DJANGO_VERSION_PICKLE_KEY: get_version()}

    def __setstate__(self, state): # same in QuerySet
        msg = None
        pickled_version = state.get(DJANGO_VERSION_PICKLE_KEY)
        if pickled_version:
            current_version = get_version()
            if current_version != pickled_version:
                msg = (
                    "Pickled MultiDBQuerySet instance's Django version %s does not "
                    "match the current version %s." % (pickled_version, current_version)
                )
        else:
            msg = "Pickled MultiDBQuerySet instance's Django version is not specified."

        if msg:
            warnings.warn(msg, RuntimeWarning, stacklevel=2)

        self.__dict__.update(state)

    def __bool__(self):
        return bool(self._chain())

    def test(self, other):
        pass

    def __and__(self, other):
        # If the other QuerySet is an EmptyQuerySet, this is a no-op.
        if isinstance(other, EmptyMultiDBQuerySet) or isinstance(other, EmptyQuerySet):
            return other
        if isinstance(self, EmptyMultiDBQuerySet):
            return self

        if other.model != self.model:
            raise TypeError( "'%s' classes must be same model." % other.__class__.__name__ )

        querysets = []

        if isinstance(other, MultiDBQuerySet):

            self.multidbquerysets.extend(other.multidbquerysets)

            for qs in self.multidbquerysets:
                querysets.append(qs.filter(Q(**self.filter_kwargs)) & qs.filter(Q(**other.filter_kwargs)))

            self.multidbquerysets = [querysets[0]]
            return self._clone()

        elif isinstance(other, QuerySet):
            
            for qs in self.multidbquerysets:
                # Only QuerySets of the same type can have any overlap.
                if issubclass(qs.model, other.model):
                    querysets.append(qs & other)

            # If none are left, we're left with an EmptyQuerySet.
            if not querysets:
                return other.none()

        else:
            raise TypeError( "'%s' classes must be MultiDBQuerySet or QuerySet." % other.__class__.__name__ )

        self.multidbquerysets = querysets
        return self._clone()

    def __or__(self, other):
        if isinstance(other, EmptyMultiDBQuerySet) or isinstance(other, EmptyQuerySet):
            return other
        if isinstance(self, EmptyMultiDBQuerySet):
            return self

        if other.model != self.model:
                raise TypeError( "'%s' classes must be same model." % other.__class__.__name__ )

        if isinstance(other, MultiDBQuerySet):

            self.multidbquerysets.extend(other.multidbquerysets)
            return self._clone()

        elif isinstance(other, QuerySet):
            
            self.multidbquerysets.append(other)
            return self._clone()

        else:
            raise TypeError( "'%s' classes must be MultiDBQuerySet or QuerySet." % other.__class__.__name__ )
  
    ####################################
    # METHODS THAT DO DATABASE QUERIES #
    ####################################

    def _set_multidbquerysets(self):

        if not self.__multidbquerysets:
            if not self._db_list: # for test
                self._db_list = Databases.objects.all().filter(model_name=self.model._meta.model_name).exclude(count=0)

            for db_name in self._db_list:
                self.multidbquerysets.append(QuerySet(model=self.model, using=str(db_name))) 
        else:
            self.multidbquerysets = self.__multidbquerysets

    def iterator(self, chunk_size=2000):
        """
        An iterator over the results from applying this QuerySet to the
        database.
        """
        pass

    def aggregate(self, *args, **kwargs):
        pass

    def count(self):
        """
        Performs a .count() for all subquerysets and returns the number of
        records as an integer.
        """
        return sum(qs.count() for qs in self.multidbquerysets)

    def get(self, **kwargs):
        clone = self.filter(**kwargs)
        querysets =[]
        result = None
        for qs in clone.multidbquerysets:
            try:
                obj = qs.get()
            except ObjectDoesNotExist:
                pass
            # Don't catch the MultipleObjectsReturned(), allow it to raise.
            else:
                # If a second object is found, raise an exception.
                if result:
                    raise MultipleObjectsReturned()
                result = obj
                querysets.append(obj)

        # Checked all QuerySets and no object was found.
        if result is None:
            raise ObjectDoesNotExist()

        # Return the only result found.
        clone.multidbquerysets = querysets
        print("clone", clone.multidbquerysets[0])
        #return clone.multidbquerysets[0]#self._clone()
        return result

    def create(self, **kwargs):
        pass

    def bulk_create(self, objs, batch_size=None, ignore_conflicts=False):
        pass

    def bulk_update(self, objs, fields, batch_size=None):
        pass

    def get_or_create(self, defaults=None, **kwargs):
        """
        Look up an object with the given kwargs, creating one if necessary.
        Return a tuple of (object, created), where created is a boolean
        specifying whether an object was created.
        """
        pass

    def update_or_create(self, defaults=None, **kwargs):
        pass

    def earliest(self, *fields):
        pass

    def latest(self, *fields):
        pass

    def first(self):
        """Return the first object of a query or None if no match is found."""
        pass

    def last(self):
        """Return the last object of a query or None if no match is found."""
        pass

    def in_bulk(self, id_list=None, *, field_name='pk'):
        pass

    def delete(self):
        pass

    def update(self, **kwargs):
        pass

    def exists(self):
        pass

    def explain(self, *, format=None, **options):
        pass

    ##################################################
    # PUBLIC METHODS THAT RETURN A QUERYSET SUBCLASS #
    ##################################################

    def raw(self, raw_query, params=None, translations=None, using=None):
        pass

    def values(self, *fields, **expressions):
        values =[]
        for qq in self.multidbquerysets:
            values.append(qq.values(*fields, **expressions))

        self.multidbquerysets  = values
        return self._clone() 

    def values_list(self, *fields, flat=False, named=False):
        values_list =[]
        for qq in self.multidbquerysets:
            values_list.append(qq.values_list(*fields, flat=flat, named=named))

        self.multidbquerysets  = values_list
        return self._clone()

    def dates(self, field_name, kind, order='ASC'):
        """
        Return a list of date objects representing all available dates for
        the given field_name, scoped to 'kind'.
        """
        dates_list =[]
        for qq in self.multidbquerysets:
            dates_list.append(qq.dates(field_name=field_name,kind=kind,order=order))

        self.multidbquerysets  = dates_list
        return self._clone()

    def datetimes(self, field_name, kind, order='ASC', tzinfo=None):
        datetimes_list =[]
        for qq in self.multidbquerysets:
            datetimes_list.append(qq.datetimes(field_name=field_name,kind=kind,order=order,tzinfo=tzinfo))

        self.multidbquerysets  = datetimes_list
        return self._clone() 

    def none(self):
        """Return an empty QuerySet."""
        empty = self.multidbquerysets[0].none()
        self.multidbquerysets = []
        self.multidbquerysets.append(empty)
        return self._clone()


    ##################################################################
    # PUBLIC METHODS THAT ALTER ATTRIBUTES AND RETURN A NEW QUERYSET #
    ##################################################################

    def all(self):# to refverify
        """
        Return a new QuerySet that is a copy of the current one. This allows a
        QuerySet to proxy for a model manager in some cases.
        """
        return self._clone()

    def filter(self, *args, **kwargs):

        self.filter_args   = args
        self.filter_kwargs = kwargs

        filtered_list =[]
        for qq in self.multidbquerysets:           
            filtered_list.append(qq.filter(*args, **kwargs) )

        self.multidbquerysets  = filtered_list

        return self._clone()

    def union(self, *other_qs, all=False):
        raise NotImplementedError()

    def complex_filter(self, filter_obj):
        complex_filter_list =[]
        for qq in self.multidbquerysets:
            complex_filter_list.append(qq.complex_filter(filter_obj=filter_obj))

        self.multidbquerysets  = complex_filter_list
        return self._clone() 

    def exclude(self, *args, **kwargs):
        exclude_list =[]
        for qq in self.multidbquerysets:
            exclude_list.append(qq.exclude(*args, **kwargs))

        self.multidbquerysets  = exclude_list
        return self._clone() 


# to complete and verify

    def intersection(self, *other_qs):
        pass

    def difference(self, *other_qs):
        pass

    def select_for_update(self, nowait=False, skip_locked=False, of=()):
        pass

    def select_related(self, *fields):  
        pass

    def prefetch_related(self, *lookups):
        pass
        
    def annotate(self, *args, **kwargs):
        pass

    def order_by(self, *field_names): # to reverify

        """Return a new QuerySet instance with the ordering changed."""
        assert not self.query.is_sliced, \
            "Cannot reorder a query once a slice has been taken."
        obj = self._clone()
        obj.query.clear_ordering(force_empty=False)
        obj.query.add_ordering(*field_names)
        return obj
        

    def distinct(self, *field_names):
        pass

    def extra(self, select=None, where=None, params=None, tables=None,
              order_by=None, select_params=None):
        pass

    def reverse(self):
        """Reverse the ordering of the QuerySet."""
        pass

    def defer(self, *fields):
        pass

    def only(self, *fields):
        pass

    def using(self, alias):
        """Select which database this QuerySet should execute against."""
        clone = self._clone()
        clone._db = alias
        return clone
        #raise NotImplementedError()

    ###################################
    # PUBLIC INTROSPECTION ATTRIBUTES #
    ###################################

    @property
    def ordered(self):
        """
        Return True if the QuerySet is ordered -- i.e. has an order_by()
        clause or a default ordering on the model (or is empty).
        """
        pass

    @property
    def db(self):
        """Return the database used if this query is executed now."""
        pass

    ###################
    # PRIVATE METHODS #
    ###################

    def _clone(self):
        return self.__class__(model=self.model, multidbquerysets = self.multidbquerysets, filter_args=self.filter_args, filter_kwargs=self.filter_kwargs)

    def _chain(self):
        return chain(*self.multidbquerysets)


class InstanceCheckMeta(type):
    def __instancecheck__(self, instance):
        if isinstance(instance, MultiDBQuerySet):
            if len(instance) == 0:
                return True
            return False
        return False
        #return isinstance(instance, MultiDBQuerySet) and instance.query.is_empty()


class EmptyMultiDBQuerySet(metaclass=InstanceCheckMeta):
    """
    Marker class to checking if a queryset is empty by .none():
        isinstance(qs.none(), EmptyQuerySet) -> True
    """

    def __init__(self, *args, **kwargs):
        raise TypeError("EmptyQuerySet can't be instantiated")
    




# class MultiDBQuerySet:
#     """Represent a lazy multidatabases lookup for a set of objects."""
#     def __init__(self, model=None, db_list=None):

#         self.model    = model
#         self._db_list = db_list

#         self._low_mark, self._high_mark = 0, None

#         self.query = sql.Query(self.model)

#         self._set_querysets() 


    
#     def as_manager(cls):
#         # Address the circular dependency between `Queryset` and `Manager`.
#         from django.db.models.manager import Manager
#         manager = Manager.from_queryset(cls)()
#         manager._built_with_as_manager = True
#         return manager
#     as_manager.queryset_only = True
#     as_manager = classmethod(as_manager)
            
#     ########################
#     # PYTHON MAGIC METHODS #
#     ########################

#     def __iter__(self):
#         """
#         The queryset iterator protocol uses three nested iterators in the
#         default case:
#             1. sql.compiler.execute_sql()
#                - Returns 100 rows at time (constants.GET_ITERATOR_CHUNK_SIZE)
#                  using cursor.fetchmany(). This part is responsible for
#                  doing some column masking, and returning the rows in chunks.
#             2. sql.compiler.results_iter()
#                - Returns one row at time. At this point the rows are still just
#                  tuples. In some cases the return values are converted to
#                  Python values at this location.
#             3. self.iterator()
#                - Responsible for turning the rows into model objects.
#         """
        
#         return list(self._clone())

#     def __getitem__(self, k):
#         """
#         Retrieves an item or slice from the set of results.
#         """
#         if not isinstance(k, (int, slice)):
#             raise TypeError
#         assert ((not isinstance(k, slice) and (k >= 0)) or
#                 (isinstance(k, slice) and (k.start is None or k.start >= 0) and
#                  (k.stop is None or k.stop >= 0))), \
#             "Negative indexing is not supported."

#         if isinstance(k, slice):
#             qs = self._clone()
#             # If start is not given, it is 0.
#             if k.start is not None:
#                 start = int(k.start)
#             else:
#                 start = 0
#             # Apply the new start to any previous slices.
#             qs._low_mark += start

#             # If stop is not given, don't modify the stop.
#             if k.stop is not None:
#                 stop = int(k.stop)

#                 # The high mark needs to take into an account any previous
#                 # offsets of the low mark.
#                 offset = stop - start
#                 qs._high_mark = qs._low_mark + offset
#             return list(qs)[::k.step] if k.step else qs

#         qs = self._clone()
#         qs._low_mark += k
#         qs._high_mark = qs._low_mark + 1
#         return list(qs)[0]

#     #def __str__(self):
#         #return self.__class__.__name__

#     def __repr__(self):
#         data = list(self[:REPR_OUTPUT_SIZE + 1])
#         if len(data) > REPR_OUTPUT_SIZE:
#             data[-1] = "...(remaining elements truncated)..."
#         return '<%s %r>' % (self.__class__.__name__, data)

#     ####################################
#     # METHODS THAT DO DATABASE QUERIES #
#     ####################################

#     def _set_querysets(self):

#         if not self._db_list: # for test
#             self._db_list = Databases.objects.all().filter(model_name=self.model._meta.model_name).exclude(count=0)

#         #for will be multithreading
#         self.querysets = []
#         #i = 0
#         for db_name in self._db_list:
#             self.querysets.append(QuerySet(model=self.model, using=str(db_name)))   

#     def count(self):
#         """
#         Performs a .count() for all subquerysets and returns the number of
#         records as an integer.
#         """
#         return sum(qs.count() for qs in self.querysets)


#     ##################################################
#     # PUBLIC METHODS THAT RETURN A QUERYSET SUBCLASS #
#     ##################################################



#     ##################################################################
#     # PUBLIC METHODS THAT ALTER ATTRIBUTES AND RETURN A NEW QUERYSET #
#     ##################################################################

#     def all(self):
#         """
#         Return a new QuerySet that is a copy of the current one. This allows a
#         QuerySet to proxy for a model manager in some cases.
#         """
#         return self._clone()

#     def filter(self, *args, **kwargs):
#         """
#         Return a new QuerySet instance with the args ANDed to the existing
#         set.
#         """
        
#         self._not_support_combined_queries('filter')
#         return self._filter_or_exclude(False, *args, **kwargs)

#     def _filter_or_exclude(self, negate, *args, **kwargs):
#         if args or kwargs:
#             assert not self.query.is_sliced, \
#                 "Cannot filter a query once a slice has been taken."

#         new_clone = []
#         for clone in self.querysets:
#             if negate:
#                 clone.query.add_q(~Q(*args, **kwargs))
#             else:
#                 clone.query.add_q(Q(*args, **kwargs))
#             new_clone.append(clone)

        
#         #return chain(*new_clone)
#         return MultiDBQuerySet_chain(new_clone, self)
    

#     ###################################
#     # PUBLIC INTROSPECTION ATTRIBUTES #
#     ###################################


#     def none(self):
#         """Return an empty QuerySet."""
#         clone = self._clone()
#         clone.query.set_empty()
#         return clone

#     ###################
#     # PRIVATE METHODS #
#     ###################

#     def _chain(self, *args):
#         return chain(*args)

#     # def _chain(self, **kwargs):
#     #     """
#     #     Return a copy of the current QuerySet that's ready for another
#     #     operation.
#     #     """
#     #     obj = self._clone()
#     #     if obj._sticky_filter:
#     #         obj.query.filter_is_sticky = True
#     #         obj._sticky_filter = False
#     #     obj.__dict__.update(kwargs)
#     #     return obj

#     def __call__(self):
#         data = list(self[:REPR_OUTPUT_SIZE + 1])
#         if len(data) > REPR_OUTPUT_SIZE:
#             data[-1] = "...(remaining elements truncated)..."
#         return '<%s %r>' % (self.__class__.__name__, data)

#     def _clone(self):
#         "Returns a clone of this queryset chain"
#         return self.__class__(model = self.model, db_list = self._db_list)

#     def _all(self):
#         "Iterates records in all subquerysets"
#         self._querysets = chain(*self.querysets)
#         return self._querysets

#     def _not_support_combined_queries(self, operation_name):
#         if self.query.combinator:
#             raise NotSupportedError(
#                 'Calling QuerySet.%s() after %s() is not supported.'
#                 % (operation_name, self.query.combinator)
#             )
    
#     def first(self):
#         """Return the first object of a query or None if no match is found."""
#         for obj in (self if self.ordered else self.order_by('pk'))[:1]:
#             return obj

#     def last(self):
#         """Return the last object of a query or None if no match is found."""
#         for obj in (self.reverse() if self.ordered else self.order_by('-pk'))[:1]:
#             return obj

# class MultiDBQuerySet_chain:

#     def __init__(self, querysets, iclass):
#         self.querysets  = querysets 
#         self.iclass     = iclass
#         self.class_name = iclass.__class__.__name__
#         self.kwargs = {}

#     def __getitem__(self, k):
#         #return list(chain(*self.querysets))
#         return chain(*self.querysets)

#     def filter(self, *args, **kwargs):
#         """
#         Return a new QuerySet instance with the args ANDed to the existing
#         set.
#         """
#         self.kwargs = {**self.kwargs, **kwargs} 
#         print(self.kwargs)
#         return self.iclass.filter(*args, **self.kwargs)

#     def __repr__(self):
#         data = list(self[:REPR_OUTPUT_SIZE + 1])
#         if len(data) > REPR_OUTPUT_SIZE:
#             data[-1] = "...(remaining elements truncated)..."
#         return '<%s %r>' % (self.class_name, data)
    


        

