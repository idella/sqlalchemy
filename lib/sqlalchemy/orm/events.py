"""ORM event interfaces.

"""
from sqlalchemy import event, exc
import inspect

class InstrumentationEvents(event.Events):
    """Events related to class instrumentation events.
    
    The listeners here support being established against
    any new style class, that is any object that is a subclass
    of 'type'.  Events will then be fired off for events
    against that class as well as all subclasses.  
    'type' itself is also accepted as a target
    in which case the events fire for all classes.
    
    """
    
    @classmethod
    def accept_with(cls, target):
        from sqlalchemy.orm.instrumentation import instrumentation_registry
        
        if isinstance(target, type):
            return instrumentation_registry
        else:
            return None

    @classmethod
    def listen(cls, target, identifier, fn, propagate=False):
        event.Events.listen(target, identifier, fn, propagate=propagate)

    @classmethod
    def remove(cls, identifier, target, fn):
        raise NotImplementedError("Removal of instrumentation events not yet implemented")

    def on_class_instrument(self, cls):
        """Called after the given class is instrumented.
        
        To get at the :class:`.ClassManager`, use
        :func:`.manager_of_class`.
        
        """

    def on_class_uninstrument(self, cls):
        """Called before the given class is uninstrumented.
        
        To get at the :class:`.ClassManager`, use
        :func:`.manager_of_class`.
        
        """
        
        
    def on_attribute_instrument(self, cls, key, inst):
        """Called when an attribute is instrumented."""

class InstanceEvents(event.Events):
    """Define events specific to object lifecycle.
    
    Instance-level don't automatically propagate their associations
    to subclasses.
    
    """
    @classmethod
    def accept_with(cls, target):
        from sqlalchemy.orm.instrumentation import ClassManager, manager_of_class
        from sqlalchemy.orm import Mapper, mapper
        
        if isinstance(target, ClassManager):
            return target
        elif isinstance(target, Mapper):
            return target.class_manager
        elif target is mapper:
            return ClassManager
        elif isinstance(target, type):
            if issubclass(target, Mapper):
                return ClassManager
            else:
                manager = manager_of_class(target)
                if manager:
                    return manager
        return None
    
    @classmethod
    def listen(cls, target, identifier, fn, raw=False, propagate=False):
        if not raw:
            orig_fn = fn
            def wrap(state, *arg, **kw):
                return orig_fn(state.obj(), *arg, **kw)
            fn = wrap

        event.Events.listen(target, identifier, fn, propagate=propagate)
        if propagate:
            for mgr in target.subclass_managers(True):
                event.Events.listen(mgr, identifier, fn, True)
            
    @classmethod
    def remove(cls, identifier, target, fn):
        raise NotImplementedError("Removal of instance events not yet implemented")

    def on_first_init(self, manager, cls):
        """Called when the first instance of a particular mapping is called.

        """
        
    def on_init(self, target, args, kwargs):
        """Receive an instance when it's constructor is called.
        
        This method is only called during a userland construction of 
        an object.  It is not called when an object is loaded from the
        database.

        """
        
    def on_init_failure(self, target, args, kwargs):
        """Receive an instance when it's constructor has been called, 
        and raised an exception.
        
        This method is only called during a userland construction of 
        an object.  It is not called when an object is loaded from the
        database.

        """
    
    def on_load(self, target):
        """Receive an object instance after it has been created via
        ``__new__``, and after initial attribute population has
        occurred.

        This typically occurs when the instance is created based on
        incoming result rows, and is only called once for that
        instance's lifetime.

        Note that during a result-row load, this method is called upon
        the first row received for this instance.  Note that some 
        attributes and collections may or may not be loaded or even 
        initialized, depending on what's present in the result rows.

        """
    
    def on_resurrect(self, target):
        """Receive an object instance as it is 'resurrected' from 
        garbage collection, which occurs when a "dirty" state falls
        out of scope."""

        
class MapperEvents(event.Events):
    """Define events specific to mappings.

    e.g.::
    
        from sqlalchemy import event

        def my_before_insert_listener(mapper, connection, target):
            # execute a stored procedure upon INSERT,
            # apply the value to the row to be inserted
            target.calculated_value = connection.scalar(
                                        "select my_special_function(%d)" 
                                        % target.special_number)
        
        # associate the listener function with SomeMappedClass,
        # to execute during the "on_before_insert" hook
        event.listen(SomeMappedClass, 'on_before_insert', my_before_insert_listener)

    Available targets include mapped classes, instances of
    :class:`.Mapper` (i.e. returned by :func:`.mapper`,
    :func:`.class_mapper` and similar), as well as the
    :class:`.Mapper` class and :func:`.mapper` function itself
    for global event reception::

        from sqlalchemy.orm import mapper
        
        def some_listener(mapper, connection, target):
            log.debug("Instance %s being inserted" % target)
            
        # attach to all mappers
        event.listen(mapper, 'on_before_insert', some_listener)
    
    Mapper events provide hooks into critical sections of the
    mapper, including those related to object instrumentation,
    object loading, and object persistence. In particular, the
    persistence methods :meth:`~.MapperEvents.on_before_insert`,
    and :meth:`~.MapperEvents.on_before_update` are popular
    places to augment the state being persisted - however, these
    methods operate with several significant restrictions. The
    user is encouraged to evaluate the
    :meth:`.SessionEvents.on_before_flush` and
    :meth:`.SessionEvents.on_after_flush` methods as more
    flexible and user-friendly hooks in which to apply
    additional database state during a flush.
    
    When using :class:`.MapperEvents`, several modifiers are
    available to the :func:`.event.listen` function.
    
    :param propagate=False: When True, the event listener should 
       be applied to all inheriting mappers as well as the 
       mapper which is the target of this listener.
    :param raw=False: When True, the "target" argument passed
       to applicable event listener functions will be the 
       instance's :class:`.InstanceState` management
       object, rather than the mapped instance itself.
    :param retval=False: when True, the user-defined event function
       must have a return value, the purpose of which is either to
       control subsequent event propagation, or to otherwise alter 
       the operation in progress by the mapper.   Possible return
       values are:
      
       * ``sqlalchemy.orm.interfaces.EXT_CONTINUE`` - continue event
         processing normally.
       * ``sqlalchemy.orm.interfaces.EXT_STOP`` - cancel all subsequent
         event handlers in the chain.
       * other values - the return value specified by specific listeners,
         such as :meth:`~.MapperEvents.on_translate_row` or 
         :meth:`~.MapperEvents.on_create_instance`.
     
    """

    @classmethod
    def accept_with(cls, target):
        from sqlalchemy.orm import mapper, class_mapper, Mapper
        if target is mapper:
            return Mapper
        elif isinstance(target, type):
            if issubclass(target, Mapper):
                return target
            else:
                return class_mapper(target)
        else:
            return target
        
    @classmethod
    def listen(cls, target, identifier, fn, 
                            raw=False, retval=False, propagate=False):
        from sqlalchemy.orm.interfaces import EXT_CONTINUE

        if not raw or not retval:
            if not raw:
                meth = getattr(cls, identifier)
                try:
                    target_index = inspect.getargspec(meth)[0].index('target') - 1
                except ValueError:
                    target_index = None
            
            wrapped_fn = fn
            def wrap(*arg, **kw):
                if not raw and target_index is not None:
                    arg = list(arg)
                    arg[target_index] = arg[target_index].obj()
                if not retval:
                    wrapped_fn(*arg, **kw)
                    return EXT_CONTINUE
                else:
                    return wrapped_fn(*arg, **kw)
            fn = wrap
        
        if propagate:
            for mapper in target.self_and_descendants:
                event.Events.listen(mapper, identifier, fn, propagate=True)
        else:
            event.Events.listen(target, identifier, fn)
        
    def on_instrument_class(self, mapper, class_):
        """Receive a class when the mapper is first constructed, and has
        applied instrumentation to the mapped class.
        
        This listener can generally only be applied to the :class:`.Mapper`
        class overall.
        
        :param mapper: the :class:`.Mapper` which is the target
         of this event.
        :param class\_: the mapped class.
        
        """

    def on_translate_row(self, mapper, context, row):
        """Perform pre-processing on the given result row and return a
        new row instance.

        This listener is typically registered with ``retval=True``.
        It is called when the mapper first receives a row, before
        the object identity or the instance itself has been derived
        from that row.   The given row may or may not be a 
        :class:`.RowProxy` object - it will always be a dictionary-like
        object which contains mapped columns as keys.  The 
        returned object should also be a dictionary-like object
        which recognizes mapped columns as keys.
        
        :param mapper: the :class:`.Mapper` which is the target
         of this event.
        :param context: the :class:`.QueryContext`, which includes
         a handle to the current :class:`.Query` in progress as well
         as additional state information.
        :param row: the result row being handled.  This may be 
         an actual :class:`.RowProxy` or may be a dictionary containing
         :class:`.Column` objects as keys.
        :return: When configured with ``retval=True``, the function
         should return a dictionary-like row object, or ``EXT_CONTINUE``,
         indicating the original row should be used.
         
        
        """

    def on_create_instance(self, mapper, context, row, class_):
        """Receive a row when a new object instance is about to be
        created from that row.

        The method can choose to create the instance itself, or it can return
        EXT_CONTINUE to indicate normal object creation should take place.
        This listener is typically registered with ``retval=True``.

        :param mapper: the :class:`.Mapper` which is the target
         of this event.
        :param context: the :class:`.QueryContext`, which includes
         a handle to the current :class:`.Query` in progress as well
         as additional state information.
        :param row: the result row being handled.  This may be 
         an actual :class:`.RowProxy` or may be a dictionary containing
         :class:`.Column` objects as keys.
        :param class\_: the mapped class.
        :return: When configured with ``retval=True``, the return value
         should be a newly created instance of the mapped class, 
         or ``EXT_CONTINUE`` indicating that default object construction
         should take place.

        """

    def on_append_result(self, mapper, context, row, target, 
                        result, **flags):
        """Receive an object instance before that instance is appended
        to a result list.
        
        This is a rarely used hook which can be used to alter
        the construction of a result list returned by :class:`.Query`.
        
        :param mapper: the :class:`.Mapper` which is the target
         of this event.
        :param context: the :class:`.QueryContext`, which includes
         a handle to the current :class:`.Query` in progress as well
         as additional state information.
        :param row: the result row being handled.  This may be 
         an actual :class:`.RowProxy` or may be a dictionary containing
         :class:`.Column` objects as keys.
        :param target: the mapped instance being populated.  If 
         the event is configured with ``raw=True``, this will 
         instead be the :class:`.InstanceState` state-management
         object associated with the instance.
        :param result: a list-like object where results are being
         appended.
        :param \**flags: Additional state information about the 
         current handling of the row.
        :return: If this method is registered with ``retval=True``,
         a return value of ``EXT_STOP`` will prevent the instance
         from being appended to the given result list, whereas a 
         return value of ``EXT_CONTINUE`` will result in the default
         behavior of appending the value to the result list.

        """


    def on_populate_instance(self, mapper, context, row, 
                            target, **flags):
        """Receive an instance before that instance has
        its attributes populated.

        This usually corresponds to a newly loaded instance but may
        also correspond to an already-loaded instance which has
        unloaded attributes to be populated.  The method may be called
        many times for a single instance, as multiple result rows are
        used to populate eagerly loaded collections.
        
        Most usages of this hook are obsolete.  For a
        generic "object has been newly created from a row" hook, use
        :meth:`.InstanceEvents.on_load`.

        :param mapper: the :class:`.Mapper` which is the target
         of this event.
        :param context: the :class:`.QueryContext`, which includes
         a handle to the current :class:`.Query` in progress as well
         as additional state information.
        :param row: the result row being handled.  This may be 
         an actual :class:`.RowProxy` or may be a dictionary containing
         :class:`.Column` objects as keys.
        :param class\_: the mapped class.
        :return: When configured with ``retval=True``, a return
         value of ``EXT_STOP`` will bypass instance population by
         the mapper. A value of ``EXT_CONTINUE`` indicates that
         default instance population should take place.

        """

    def on_before_insert(self, mapper, connection, target):
        """Receive an object instance before an INSERT statement
        is emitted corresponding to that instance.
        
        This event is used to modify local, non-object related 
        attributes on the instance before an INSERT occurs, as well
        as to emit additional SQL statements on the given 
        connection.   
        
        The event is often called for a batch of objects of the
        same class before their INSERT statements are emitted at
        once in a later step. In the extremely rare case that
        this is not desirable, the :func:`.mapper` can be
        configured with ``batch=False``, which will cause
        batches of instances to be broken up into individual
        (and more poorly performing) event->persist->event
        steps.
        
        Handlers should **not** modify any attributes which are
        mapped by :func:`.relationship`, nor should they attempt
        to make any modifications to the :class:`.Session` in
        this hook (including :meth:`.Session.add`, 
        :meth:`.Session.delete`, etc.) - such changes will not
        take effect. For overall changes to the "flush plan",
        use :meth:`.SessionEvents.before_flush`.

        :param mapper: the :class:`.Mapper` which is the target
         of this event.
        :param connection: the :class:`.Connection` being used to 
         emit INSERT statements for this instance.  This
         provides a handle into the current transaction on the 
         target database specific to this instance.
        :param target: the mapped instance being persisted.  If 
         the event is configured with ``raw=True``, this will 
         instead be the :class:`.InstanceState` state-management
         object associated with the instance.
        :return: No return value is supported by this event.

        """

    def on_after_insert(self, mapper, connection, target):
        """Receive an object instance after an INSERT statement
        is emitted corresponding to that instance.
        
        This event is used to modify in-Python-only
        state on the instance after an INSERT occurs, as well
        as to emit additional SQL statements on the given 
        connection.   

        The event is often called for a batch of objects of the
        same class after their INSERT statements have been
        emitted at once in a previous step. In the extremely
        rare case that this is not desirable, the
        :func:`.mapper` can be configured with ``batch=False``,
        which will cause batches of instances to be broken up
        into individual (and more poorly performing)
        event->persist->event steps.

        :param mapper: the :class:`.Mapper` which is the target
         of this event.
        :param connection: the :class:`.Connection` being used to 
         emit INSERT statements for this instance.  This
         provides a handle into the current transaction on the 
         target database specific to this instance.
        :param target: the mapped instance being persisted.  If 
         the event is configured with ``raw=True``, this will 
         instead be the :class:`.InstanceState` state-management
         object associated with the instance.
        :return: No return value is supported by this event.
        
        """

    def on_before_update(self, mapper, connection, target):
        """Receive an object instance before an UPDATE statement
        is emitted corresponding to that instance.

        This event is used to modify local, non-object related 
        attributes on the instance before an UPDATE occurs, as well
        as to emit additional SQL statements on the given 
        connection.   

        This method is called for all instances that are
        marked as "dirty", *even those which have no net changes
        to their column-based attributes*. An object is marked
        as dirty when any of its column-based attributes have a
        "set attribute" operation called or when any of its
        collections are modified. If, at update time, no
        column-based attributes have any net changes, no UPDATE
        statement will be issued. This means that an instance
        being sent to :meth:`~.MapperEvents.on_before_update` is
        *not* a guarantee that an UPDATE statement will be
        issued, although you can affect the outcome here by
        modifying attributes so that a net change in value does
        exist.
        
        To detect if the column-based attributes on the object have net
        changes, and will therefore generate an UPDATE statement, use
        ``object_session(instance).is_modified(instance,
        include_collections=False)``.

        The event is often called for a batch of objects of the
        same class before their UPDATE statements are emitted at
        once in a later step. In the extremely rare case that
        this is not desirable, the :func:`.mapper` can be
        configured with ``batch=False``, which will cause
        batches of instances to be broken up into individual
        (and more poorly performing) event->persist->event
        steps.
        
        Handlers should **not** modify any attributes which are
        mapped by :func:`.relationship`, nor should they attempt
        to make any modifications to the :class:`.Session` in
        this hook (including :meth:`.Session.add`, 
        :meth:`.Session.delete`, etc.) - such changes will not
        take effect. For overall changes to the "flush plan",
        use :meth:`.SessionEvents.before_flush`.

        :param mapper: the :class:`.Mapper` which is the target
         of this event.
        :param connection: the :class:`.Connection` being used to 
         emit UPDATE statements for this instance.  This
         provides a handle into the current transaction on the 
         target database specific to this instance.
        :param target: the mapped instance being persisted.  If 
         the event is configured with ``raw=True``, this will 
         instead be the :class:`.InstanceState` state-management
         object associated with the instance.
        :return: No return value is supported by this event.
        """

    def on_after_update(self, mapper, connection, target):
        """Receive an object instance after an UPDATE statement
        is emitted corresponding to that instance.

        This event is used to modify in-Python-only
        state on the instance after an UPDATE occurs, as well
        as to emit additional SQL statements on the given 
        connection.   

        This method is called for all instances that are
        marked as "dirty", *even those which have no net changes
        to their column-based attributes*, and for which 
        no UPDATE statement has proceeded. An object is marked
        as dirty when any of its column-based attributes have a
        "set attribute" operation called or when any of its
        collections are modified. If, at update time, no
        column-based attributes have any net changes, no UPDATE
        statement will be issued. This means that an instance
        being sent to :meth:`~.MapperEvents.on_after_update` is
        *not* a guarantee that an UPDATE statement has been
        issued.
        
        To detect if the column-based attributes on the object have net
        changes, and therefore resulted in an UPDATE statement, use
        ``object_session(instance).is_modified(instance,
        include_collections=False)``.

        The event is often called for a batch of objects of the
        same class after their UPDATE statements have been emitted at
        once in a previous step. In the extremely rare case that
        this is not desirable, the :func:`.mapper` can be
        configured with ``batch=False``, which will cause
        batches of instances to be broken up into individual
        (and more poorly performing) event->persist->event
        steps.
        
        :param mapper: the :class:`.Mapper` which is the target
         of this event.
        :param connection: the :class:`.Connection` being used to 
         emit UPDATE statements for this instance.  This
         provides a handle into the current transaction on the 
         target database specific to this instance.
        :param target: the mapped instance being persisted.  If 
         the event is configured with ``raw=True``, this will 
         instead be the :class:`.InstanceState` state-management
         object associated with the instance.
        :return: No return value is supported by this event.
        
        """

    def on_before_delete(self, mapper, connection, target):
        """Receive an object instance before a DELETE statement
        is emitted corresponding to that instance.
        
        This event is used to emit additional SQL statements on 
        the given connection as well as to perform application
        specific bookkeeping related to a deletion event.
        
        The event is often called for a batch of objects of the
        same class before their DELETE statements are emitted at
        once in a later step. 
        
        Handlers should **not** modify any attributes which are
        mapped by :func:`.relationship`, nor should they attempt
        to make any modifications to the :class:`.Session` in
        this hook (including :meth:`.Session.add`, 
        :meth:`.Session.delete`, etc.) - such changes will not
        take effect. For overall changes to the "flush plan",
        use :meth:`.SessionEvents.before_flush`.

        :param mapper: the :class:`.Mapper` which is the target
         of this event.
        :param connection: the :class:`.Connection` being used to 
         emit DELETE statements for this instance.  This
         provides a handle into the current transaction on the 
         target database specific to this instance.
        :param target: the mapped instance being deleted.  If 
         the event is configured with ``raw=True``, this will 
         instead be the :class:`.InstanceState` state-management
         object associated with the instance.
        :return: No return value is supported by this event.
        
        """

    def on_after_delete(self, mapper, connection, target):
        """Receive an object instance after a DELETE statement
        has been emitted corresponding to that instance.
        
        This event is used to emit additional SQL statements on 
        the given connection as well as to perform application
        specific bookkeeping related to a deletion event.
        
        The event is often called for a batch of objects of the
        same class after their DELETE statements have been emitted at
        once in a previous step. 

        :param mapper: the :class:`.Mapper` which is the target
         of this event.
        :param connection: the :class:`.Connection` being used to 
         emit DELETE statements for this instance.  This
         provides a handle into the current transaction on the 
         target database specific to this instance.
        :param target: the mapped instance being deleted.  If 
         the event is configured with ``raw=True``, this will 
         instead be the :class:`.InstanceState` state-management
         object associated with the instance.
        :return: No return value is supported by this event.
        
        """

    @classmethod
    def remove(cls, identifier, target, fn):
        raise NotImplementedError("Removal of mapper events not yet implemented")
    
class SessionEvents(event.Events):
    """Define events specific to :class:`.Session` lifecycle.
    
    e.g.::
    
        from sqlalchemy import event
        from sqlalchemy.orm import sessionmaker
        
        class my_before_commit(session):
            print "before commit!"
        
        Session = sessionmaker()
        
        event.listen(Session, "on_before_commit", my_before_commit)
    
    The :func:`~.event.listen` function will accept
    :class:`.Session` objects as well as the return result
    of :func:`.sessionmaker` and :func:`.scoped_session`.
    
    Additionally, it accepts the :class:`.Session` class which
    will apply listeners to all :class:`.Session` instances
    globally.
        
    """

    @classmethod
    def accept_with(cls, target):
        from sqlalchemy.orm import ScopedSession, Session
        if isinstance(target, ScopedSession):
            if not isinstance(target.session_factory, type) or \
                not issubclass(target.session_factory, Session):
                raise exc.ArgumentError(
                            "Session event listen on a ScopedSession "
                            "requries that its creation callable "
                            "is a Session subclass.")
            return target.session_factory
        elif isinstance(target, type):
            if issubclass(target, ScopedSession):
                return Session
            elif issubclass(target, Session):
                return target
        elif isinstance(target, Session):
            return target
        else:
            return None
        
    @classmethod
    def remove(cls, identifier, target, fn):
        raise NotImplementedError("Removal of session events not yet implemented")

    def on_before_commit(self, session):
        """Execute before commit is called.
        
        Note that this may not be per-flush if a longer running
        transaction is ongoing."""

    def on_after_commit(self, session):
        """Execute after a commit has occured.
        
        Note that this may not be per-flush if a longer running
        transaction is ongoing."""

    def on_after_rollback(self, session):
        """Execute after a rollback has occured.
        
        Note that this may not be per-flush if a longer running
        transaction is ongoing."""

    def on_before_flush( self, session, flush_context, instances):
        """Execute before flush process has started.
        
        `instances` is an optional list of objects which were passed to
        the ``flush()`` method. """

    def on_after_flush(self, session, flush_context):
        """Execute after flush has completed, but before commit has been
        called.
        
        Note that the session's state is still in pre-flush, i.e. 'new',
        'dirty', and 'deleted' lists still show pre-flush state as well
        as the history settings on instance attributes."""

    def on_after_flush_postexec(self, session, flush_context):
        """Execute after flush has completed, and after the post-exec
        state occurs.
        
        This will be when the 'new', 'dirty', and 'deleted' lists are in
        their final state.  An actual commit() may or may not have
        occured, depending on whether or not the flush started its own
        transaction or participated in a larger transaction. """

    def on_after_begin( self, session, transaction, connection):
        """Execute after a transaction is begun on a connection
        
        `transaction` is the SessionTransaction. This method is called
        after an engine level transaction is begun on a connection. """

    def on_after_attach(self, session, instance):
        """Execute after an instance is attached to a session.
        
        This is called after an add, delete or merge. """

    def on_after_bulk_update( self, session, query, query_context, result):
        """Execute after a bulk update operation to the session.
        
        This is called after a session.query(...).update()
        
        `query` is the query object that this update operation was
        called on. `query_context` was the query context object.
        `result` is the result object returned from the bulk operation.
        """

    def on_after_bulk_delete( self, session, query, query_context, result):
        """Execute after a bulk delete operation to the session.
        
        This is called after a session.query(...).delete()
        
        `query` is the query object that this delete operation was
        called on. `query_context` was the query context object.
        `result` is the result object returned from the bulk operation.
        """


class AttributeEvents(event.Events):
    """Define events for object attributes.
    
    These are typically defined on the class-bound descriptor for the
    target class.

    e.g.::
    
        from sqlalchemy import event
        
        def my_append_listener(target, value, initiator):
            print "received append event for target: %s" % target
        
        event.listen(MyClass.collection, 'on_append', my_append_listener)
    
    Listeners have the option to return a possibly modified version
    of the value, when the ``retval=True`` flag is passed
    to :func:`~.event.listen`::
    
        def validate_phone(target, value, oldvalue, initiator):
            "Strip non-numeric characters from a phone number"
        
            return re.sub(r'(?![0-9])', '', value)
        
        # setup listener on UserContact.phone attribute, instructing
        # it to use the return value
        listen(UserContact.phone, 'on_set', validate_phone, retval=True)
    
    A validation function like the above can also raise an exception
    such as :class:`ValueError` to halt the operation.
        
    Several modifiers are available to the :func:`~.event.listen` function.
    
    :param active_history=False: When True, indicates that the
      "on_set" event would like to receive the "old" value being
      replaced unconditionally, even if this requires firing off
      database loads. Note that ``active_history`` can also be
      set directly via :func:`.column_property` and
      :func:`.relationship`.

    :param propagate=False: When True, the listener function will
      be established not just for the class attribute given, but
      for attributes of the same name on all current subclasses 
      of that class, as well as all future subclasses of that 
      class, using an additional listener that listens for 
      instrumentation events.
    :param raw=False: When True, the "target" argument to the
      event will be the :class:`.InstanceState` management
      object, rather than the mapped instance itself.
    :param retval=False: when True, the user-defined event 
      listening must return the "value" argument from the 
      function.  This gives the listening function the opportunity
      to change the value that is ultimately used for a "set"
      or "append" event.   
    
    """
    
    @classmethod
    def listen(cls, target, identifier, fn, active_history=False, 
                                        raw=False, retval=False,
                                        propagate=False):
        if active_history:
            target.dispatch.active_history = True
        
        # TODO: for removal, need to package the identity
        # of the wrapper with the original function.
        
        if not raw or not retval:
            orig_fn = fn
            def wrap(target, value, *arg):
                if not raw:
                    target = target.obj()
                if not retval:
                    orig_fn(target, value, *arg)
                    return value
                else:
                    return orig_fn(target, value, *arg)
            fn = wrap
            
        event.Events.listen(target, identifier, fn, propagate)
        
        if propagate:
            from sqlalchemy.orm.instrumentation import manager_of_class
            
            manager = manager_of_class(target.class_)
            
            for mgr in manager.subclass_managers(True):
                event.Events.listen(mgr[target.key], identifier, fn, True)
        
    @classmethod
    def remove(cls, identifier, target, fn):
        raise NotImplementedError("Removal of attribute events not yet implemented")
        
    def on_append(self, target, value, initiator):
        """Receive a collection append event.

        :param target: the object instance receiving the event.
          If the listener is registered with ``raw=True``, this will
          be the :class:`.InstanceState` object.
        :param value: the value being appended.  If this listener
          is registered with ``retval=True``, the listener
          function must return this value, or a new value which 
          replaces it.
        :param initiator: the attribute implementation object 
          which initiated this event.
        :return: if the event was registered with ``retval=True``,
         the given value, or a new effective value, should be returned.
         
        """

    def on_remove(self, target, value, initiator):
        """Receive a collection remove event.

        :param target: the object instance receiving the event.
          If the listener is registered with ``raw=True``, this will
          be the :class:`.InstanceState` object.
        :param value: the value being removed.
        :param initiator: the attribute implementation object 
          which initiated this event.
        :return: No return value is defined for this event.
        """

    def on_set(self, target, value, oldvalue, initiator):
        """Receive a scalar set event.

        :param target: the object instance receiving the event.
          If the listener is registered with ``raw=True``, this will
          be the :class:`.InstanceState` object.
        :param value: the value being set.  If this listener
          is registered with ``retval=True``, the listener
          function must return this value, or a new value which 
          replaces it.
        :param oldvalue: the previous value being replaced.  This
          may also be the symbol ``NEVER_SET`` or ``NO_VALUE``.
          If the listener is registered with ``active_history=True``,
          the previous value of the attribute will be loaded from
          the database if the existing value is currently unloaded 
          or expired.
        :param initiator: the attribute implementation object 
          which initiated this event.
        :return: if the event was registered with ``retval=True``,
         the given value, or a new effective value, should be returned.

        """
