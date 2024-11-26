=================================
Station Configuration in Simfleet
=================================


QueueStationAgent with QueueBehaviour
=====================================

The queue management behaviour in `QueueStationAgent` focuses on the organisation, supervision, and handling of queues associated with
specific services. The class implements a cyclic behaviour called QueueBehaviour, which is responsible for processing incoming requests,
handling cancellations, and updating the status of the queues.

Key Features
------------

#. **Organisation of Agents in Waiting Lists:** Each type of service has its own queue (implemented as a deque), allowing clear and efficient management. Agents can be added to the end of the queue or removed, either in FIFO order or by specific identifier.

#. **Request Management:** Upon receiving a request, the behaviour evaluates whether the requesting agent is sufficiently close to the offered service. Only then is the request accepted. If the agent meets the conditions, it is added to the corresponding queue and sent a confirmation. Otherwise, a rejection response is sent.

#. **Request Cancellation:** Agents cancelling their requests are removed from the corresponding queue. The removal is notified via messages to the simulator or the relevant agent.

#. **State Query and Update:** Queues can be queried to check their size, an agent's position in the list, or details of the waiting agents. Queues are dynamically updated based on incoming and outgoing requests.

#. **Geographic Verification:** The proximity between the requesting agent and the station is checked before accepting the agent into the queue. Requests are rejected if the agent is not within a 100-metre range.


Main Methods
------------

.. code-block:: python


    def total_queue_size(self, service_name):
    def queue_agent_to_waiting_list(self, service_name, id_agent, **kwargs):
    def dequeue_first_agent_to_waiting_list(self, service_name):
    def dequeue_agent_to_waiting_list(self, service_name, id_agent):
    def find_queue_position(self, service_name, agent_id):
    def get_queue(self, service_name):
    async def accept_request_agent(self, agent_id, content=None):
    async def refuse_request_agent(self, agent_id):

* ``total_queue_size()``
Returns the total size of the queue associated with a specific service.

* ``queue_agent_to_waiting_list()``
Adds an agent to the waiting list of a specified service.

* ``dequeue_first_agent_to_waiting_list()``
Removes and retrieves the first agent from the waiting list of a service.

* ``find_queue_position()``
Finds the position of an agent in the queue for a specific service.

* ``accept_request_agent()``
Accepts a request from an agent and sends a positive response.

* ``refuse_request_agent()``
Rejects a request from an agent and sends a negative response.


ServiceStationAgent with ServiceRunBehaviour
============================================

The `ServiceStationAgent` includes a behaviour called `ServiceRunBehaviour`, which dynamically manages the services offered by the station.
This behaviour operates in a continuous cycle to process requests from agents in the waiting queue and assign them a service if slots are
available. Below is a detailed explanation of how this behaviour works:

Key Features
------------

#. **Continuous Processing:** The behaviour continuously iterates through the waiting lists associated with each available service.

#. **Service Assignment:** Checks for available slots for a specific service. If a slot is available, it removes the first agent from the queue and assigns it to the corresponding service.

#. **Slot Updates:** Increases the number of slots in use when an agent begins receiving a service. Decreases the slots in use when an agent completes the service.

#. **Agent Notifications:** Sends informational messages to agents when their service begins or when their request is rejected due to unavailability.

#. **Specific Behaviours:** Each service can execute a specific behaviour, represented by a subclass of `OneShotBehaviour`, which can perform tasks such as charging an electric vehicle or refuelling.


Main Methods
------------

.. code-block:: python


    def increase_slots_used(self, service_type):
    def decrease_slots_used(self, service_type):
    def get_slot_number(self, service_type):
    def get_slot_number_used(self, service_type):
    async def refuse_service(self, agent_id, content=None):
    async def inform_service(self, agent_id, content=None):

* ``increase_slots_used()``
Increases the number of slots in use for a specific service.

* ``decrease_slots_used()``
Decreases the number of slots in use for a specific service.

* ``get_slot_number()``
Returns the total number of slots configured for a specific service.

* ``get_slot_number_used()``
Returns the number of slots currently in use for a specific service.

* ``refuse_service()``
Rejects an agent's service request and sends a notification message.

* ``inform_service()``
Notifies an agent that it has been assigned to a service.
