===============
Server concepts
===============

For the OpenStack Compute API, a server is a virtual machine (VM) instance,
a physical machine or a container.

Server status
~~~~~~~~~~~~~

You can filter the list of servers by image, flavor, name, and status
through the respective query parameters.

Servers contain a status attribute that indicates the current server
state. You can filter on the server status when you complete a list
servers request. The server status is returned in the response body. The
server status is one of the following values:

**Server status values**

-  ``ACTIVE``: The server is active.

-  ``BUILD``: The server has not finished the original build process.

-  ``DELETED``: The server is deleted.

-  ``ERROR``: The server is in error.

-  ``HARD_REBOOT``: The server is hard rebooting. This is equivalent to
   pulling the power plug on a physical server, plugging it back in, and
   rebooting it.

-  ``PASSWORD``: The password is being reset on the server.

-  ``REBOOT``: The server is in a soft reboot state. A reboot command
   was passed to the operating system.

-  ``REBUILD``: The server is currently being rebuilt from an image.

-  ``RESCUE``: The server is in rescue mode.

-  ``RESIZE``: Server is performing the differential copy of data that
   changed during its initial copy. Server is down for this stage.

-  ``REVERT_RESIZE``: The resize or migration of a server failed for
   some reason. The destination server is being cleaned up and the
   original source server is restarting.

-  ``SHUTOFF``: The virtual machine (VM) was powered down by the user,
   but not through the OpenStack Compute API. For example, the user
   issued a ``shutdown -h`` command from within the server instance. If
   the OpenStack Compute manager detects that the VM was powered down,
   it transitions the server instance to the SHUTOFF status. If you use
   the OpenStack Compute API to restart the instance, the instance might
   be deleted first, depending on the value in the
   *``shutdown_terminate``* database field on the Instance model.

-  ``SUSPENDED``: The server is suspended, either by request or
   necessity. This status appears for only the following hypervisors:
   XenServer/XCP, KVM, and ESXi. Administrative users may suspend an
   instance if it is infrequently used or to perform system maintenance.
   When you suspend an instance, its VM state is stored on disk, all
   memory is written to disk, and the virtual machine is stopped.
   Suspending an instance is similar to placing a device in hibernation;
   memory and vCPUs become available to create other instances.

-  ``UNKNOWN``: The state of the server is unknown. Contact your cloud
   provider.

-  ``VERIFY_RESIZE``: System is awaiting confirmation that the server is
   operational after a move or resize.

The compute provisioning algorithm has an anti-affinity property that
attempts to spread customer VMs across hosts. Under certain situations,
VMs from the same customer might be placed on the same host. hostId
represents the host your server runs on and can be used to determine
this scenario if it is relevant to your application.

.. note:: HostId is unique *per account* and is not globally unique.

Server creation
~~~~~~~~~~~~~~~

Status Transition:

``BUILD``

``ACTIVE``

``BUILD``

``ERROR`` (on error)

When you create a server, the operation asynchronously provisions a new
server. The progress of this operation depends on several factors
including location of the requested image, network I/O, host load, and
the selected flavor. The progress of the request can be checked by
performing a **GET** on /servers/*``id``*, which returns a progress
attribute (from 0% to 100% complete). The full URL to the newly created
server is returned through the ``Location`` header and is available as a
``self`` and ``bookmark`` link in the server representation. Note that
when creating a server, only the server ID, its links, and the
administrative password are guaranteed to be returned in the request.
You can retrieve additional attributes by performing subsequent **GET**
operations on the server.

Server actions
~~~~~~~~~~~~~~~

-  **Reboot**

   Use this function to perform either a soft or hard reboot of a
   server. With a soft reboot, the operating system is signaled to
   restart, which allows for a graceful shutdown of all processes. A
   hard reboot is the equivalent of power cycling the server. The
   virtualization platform should ensure that the reboot action has
   completed successfully even in cases in which the underlying
   domain/VM is paused or halted/stopped.

-  **Rebuild**

   Use this function to remove all data on the server and replaces it
   with the specified image. Server ID and IP addresses remain the same.

-  **Resize**

   Use this function to convert an existing server to a different
   flavor, in essence, scaling the server up or down. The original
   server is saved for a period of time to allow rollback if there is a
   problem. All resizes should be tested and explicitly confirmed, at
   which time the original server is removed. All resizes are
   automatically confirmed after 24 hours if you do not confirm or
   revert them.

-  **Pause**

   You can pause a server by making a pause request. This request stores
   the state of the VM in RAM. A paused instance continues to run in a
   frozen state.

-  **Suspend**

   Administrative users might want to suspend an instance if it is
   infrequently used or to perform system maintenance. When you suspend
   an instance, its VM state is stored on disk, all memory is written to
   disk, and the virtual machine is stopped. Suspending an instance is
   similar to placing a device in hibernation; memory and vCPUs become
   available to create other instances.

TODO - need to add many more actions in here

Server passwords
~~~~~~~~~~~~~~~~

You can specify a password when you create the server through the
optional adminPass attribute. The specified password must meet the
complexity requirements set by your OpenStack Compute provider. The
server might enter an ``ERROR`` state if the complexity requirements are
not met. In this case, a client can issue a change password action to
reset the server password.

If a password is not specified, a randomly generated password is
assigned and returned in the response object. This password is
guaranteed to meet the security requirements set by the compute
provider. For security reasons, the password is not returned in
subsequent **GET** calls.

Server metadata
~~~~~~~~~~~~~~~

Custom server metadata can also be supplied at launch time. The maximum
size of the metadata key and value is 255 bytes each. The maximum number
of key-value pairs that can be supplied per server is determined by the
compute provider and may be queried via the maxServerMeta absolute
limit.

Server networks
~~~~~~~~~~~~~~~

Networks to which the server connects can also be supplied at launch
time. One or more networks can be specified. User can also specify a
specific port on the network or the fixed IP address to assign to the
server interface.

Server personality
~~~~~~~~~~~~~~~~~~

You can customize the personality of a server instance by injecting data
into its file system. For example, you might want to insert ssh keys,
set configuration files, or store data that you want to retrieve from
inside the instance. This feature provides a minimal amount of
launch-time personalization. If you require significant customization,
create a custom image.

Follow these guidelines when you inject files:

-  The maximum size of the file path data is 255 bytes.

-  Encode the file contents as a Base64 string. The maximum size of the
   file contents is determined by the compute provider and may vary
   based on the image that is used to create the server

Considerations
~~~~~~~~~~~~~~

   The maximum limit refers to the number of bytes in the decoded data
   and not the number of characters in the encoded data.

-  You can inject text files only. You cannot inject binary or zip files
   into a new build.

-  The maximum number of file path/content pairs that you can supply is
   also determined by the compute provider and is defined by the
   maxPersonality absolute limit.

-  The absolute limit, maxPersonalitySize, is a byte limit that is
   guaranteed to apply to all images in the deployment. Providers can
   set additional per-image personality limits.

The file injection might not occur until after the server is built and
booted.

During file injection, any existing files that match specified files are
renamed to include the BAK extension appended with a time stamp. For
example, if the ``/etc/passwd`` file exists, it is backed up as
``/etc/passwd.bak.1246036261.5785``.

After file injection, personality files are accessible by only system
administrators. For example, on Linux, all files have root and the root
group as the owner and group owner, respectively, and allow user and
group read access only (octal 440).

Server access addresses
~~~~~~~~~~~~~~~~~~~~~~~

In a hybrid environment, the IP address of a server might not be
controlled by the underlying implementation. Instead, the access IP
address might be part of the dedicated hardware; for example, a
router/NAT device. In this case, the addresses provided by the
implementation cannot actually be used to access the server (from
outside the local LAN). Here, a separate *access address* may be
assigned at creation time to provide access to the server. This address
may not be directly bound to a network interface on the server and may
not necessarily appear when a server's addresses are queried.
Nonetheless, clients that must access the server directly are encouraged
to do so via an access address. In the example below, an IPv4 address is
assigned at creation time.


**Example: Create server with access IP: JSON request**

.. code::

    {
       "server":{
          "name":"new-server-test",
          "imageRef":"52415800-8b69-11e0-9b19-734f6f006e54",
          "flavorRef":"52415800-8b69-11e0-9b19-734f1195ff37",
          "accessIPv4":"67.23.10.132"
       }
    }

.. note:: Both IPv4 and IPv6 addresses may be used as access addresses and both
   addresses may be assigned simultaneously as illustrated below. Access
   addresses may be updated after a server has been created.


**Example: Create server with multiple access IPs: JSON request**

.. code::

    {
       "server":{
          "name":"new-server-test",
          "imageRef":"52415800-8b69-11e0-9b19-734f6f006e54",
          "flavorRef":"52415800-8b69-11e0-9b19-734f1195ff37",
          "accessIPv4":"67.23.10.132",
          "accessIPv6":"::babe:67.23.10.132"
       }
    }
