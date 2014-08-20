import waltz
from waltz import SupportingCast, SupportingActor, Cut
import time
import multiprocessing
import wrap
from wrap import manipulations

class SquarePrintingCast(SupportingCast):
  def __init__(self, **kwargs):
    SupportingCast.__init__(self, **kwargs)
    self.outbox = multiprocessing.Manager().Queue()
  
  @staticmethod
  def receive(message, **actor_kwargs):
    print "received: " + str(message)
    actor_kwargs['outbox'].put(message)


# class UIFetcher(SupportingActor):
#   def __init__(self, **kwargs):
#     SupportingActor.__init__(self, **kwargs)
#     self.MAX_TRIES = 'debug'
#     self.REPLICA_DB = wrap.Db(preset = 'replica', max_tries = self.MAX_TRIES)
#     self.USER_INFOS_SQL = """
#       SELECT 
#         u.id as user_id
#         ,{client_id} as client_id
#         ,if(ui.welcome_send_id is null, false, true) as received_welcome
#         ,if(ui.sending_credential_id in {credential_ids}, ui.sending_credential_id, null) as sending_credential_id
#         ,if(ui.sending_strategy_id in {strategy_ids}, ui.sending_strategy_id, null) as sending_strategy_id
#       FROM 
#         users u
#       LEFT JOIN
#         user_infos ui on (u.id = ui.user_id and ui.client_id = {client_id})
#       WHERE
#         u.id in {user_ids}
#     """
#     self.client_partition = wrap.iter_partition(wrap.execute('select id from clients', self.REPLICA_DB, return_frame = True).id.tolist(), 'client_id')
#     self.credential_ids = manipulations.column_to_check_inclusion(wrap.execute('select id from sending_credentials where active = 1', self.REPLICA_DB, return_frame = True).id.tolist(), literal = False, num = 1)
#     self.strategy_ids =   manipulations.column_to_check_inclusion(wrap.execute('select id from sending_strategies',                   self.REPLICA_DB, return_frame = True).id.tolist(), literal = False, num = 1)
#     self.outbox = multiprocessing.Manager().Queue()
  
#   @staticmethod  
#   def receive(user_df, **instance_kwargs):
#     print user_df
#     if user_df is None:
#       return
#     if user_df.shape[0] == 0:
#       return
#     other_partition = wrap.from_dict_list_partition({
#       'user_ids' : manipulations.column_to_check_inclusion(user_df.index.get_level_values('user_id').tolist(), literal = False, num = 1),
#       'credential_ids' : instance_kwargs['credential_ids'],
#       'strategy_ids' : instance_kwargs['strategy_ids']
#     })
#     my_workers = wrap.Workers(1)
#     instance_kwargs['outbox'].put(my_workers.execute(
#       query = instance_kwargs['USER_INFOS_SQL'],
#       db = instance_kwargs['REPLICA_DB'],
#       return_frame = True,
#       partitions = [instance_kwargs['client_partition'], other_partition],
#       reduce_operation = pd.concat
#     ))

class UIFetcher(SupportingActor):
  def __init__(self, **kwargs):
    SupportingActor.__init__(self, **kwargs)
    self.outbox = multiprocessing.Manager().Queue()
  
  @staticmethod  
  def receive(message, **actor_kwargs):
    print message
    outbox = actor_kwargs['outbox']
    outbox.put(user_df)





