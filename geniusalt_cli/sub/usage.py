class Usage(object):
    @staticmethod
    def usage():
        print("""
===================================
Usage:
    gnsalt command [<object options>] [<LongTerms options>]

===> Command list:
    scan            Auto add Modules or Nodes. This will also update a module if pillar.json has changed.
                    Supported options: '-m', '-n'
    add             To add a Module, Instance or Node.
                    Supported options: '-n','-e','-m','-pr', '-po', '-i','-p','-mb'
    del/delete      To delete Modules, Instances or Nodes.
                    Supported options: '-n', '-m', '-i'
    show            To show data of Modules, Instances or Nodes.
                    Supported options: '-n', '-m', '-i', '--short', '--instance'
    pset            To set pillar of instance.
                    Supported options: '-i' , '-p', '-e'
    pdel            To remove pillar from a instance.
                    Supported options: '-i' , '-p', '-e'
    eset            To set environment of a node.
                    Supported options: '-n' , '-e'
    include         To set instances to include other instances.
                    Supported options: '-i' , '-ii'
    exclude         To set instances to exclude included instances.
                    Supported options: '-i' , '-ii'
    bind            To set nodes to bind instances or modules. This is only set on DB level, not apply to the real hosts.
                    Supported options: '-n', '-i', '-m'
    unbind          To set nodes to unbind instances or modules. This is only set on DB level, not apply to the real hosts.
                    Supported options: '-n', '-i', '-m'
    push            To apply instances or modules to the real hosts(nodes). This will make real change on hosts.
                    Supported options: '-n', '-m', '-i', '--checkself', '--only-module'
                    If '-i' or '-m' objects specified, only the specified instances or modules will be applied, not the whole pillar bound to this node.
    lock            To lock objects to prevent it to be pushed to a real host.
                    If to push an locked object, An error will be given.
                    Supported options: '-n', '-m', '-i'
    unlock          To unlock locked objects.
                    Supported options: '-n', '-m', '-i'
    showb           To show nodes which has bound the specified instance or module.
                    Supported options: '-i', '-m'

===> object options:
    -n node1,node2,...
        To specify 'Node' basic objects.

    -m mod1,mod2,...
        To specify 'Module' basic objects.

    -pr var1,var2,var3...
        To specify pillar variables required for a module. Only available when to 'add' a module manually.

    -po var1,var2,var3...
        To specify optional pillar variables for a module. Only available when to 'add' a module manually.

    -i instance1,instance2,...
        To specify 'Instance' basic objects.

    -mb mod
        To specify module_belong when to add a instance. Only available when to 'add' an instance.

    -ii instance1,instance2,...
        To specify instances to be included. Only available for 'include' command.
        If an instance which included others instances bound to a node, key '__include__' will be auto added as a pillar variable of this instance, which value is a dict included pillars of other instances.

    -p var1=value1,var2=value2,...
        To specify 'pillar' data. this requires that value of pillars could not contain characters like '=' and ','.
        When comes with 'pdel' command, value can be ignored in your command-line just like: 'pdel -p var1,var2,var3'.

    -e envronment
        To specify envronment for nodes or pillar. Do not support multi-values seporated by ','.

===> LongTerms:
    --short
        Available for 'show' and 'showb' command.
        To show only object names, not all attributes of object.

    --instance
        Only available when to 'show' modules.
        To show instances of a module.

    --only-module
        Only available for 'push' command.
        To push nodes with only module level. This means no pillar of any instance passed to saltstack.
        This LongTerm cannot used with '-i' option at the same time.

    --checkself
        Only available for 'push' command.
        If this LongTerm specified, pillars passed to saltstack will auto add with a module level key '__checkself__', which value is equal the whole pillar of the corresponding node.
        This is sometimes useful when you want to know the whole pillar of this node, but you also want to push only specified instances or modules to the real host, which will not give the whole pillar of this node to saltstack.  

===================================""")
