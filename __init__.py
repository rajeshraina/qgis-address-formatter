def classFactory(iface):
    from .address_formatter_plugin import AddressFormatterPlugin
    return AddressFormatterPlugin(iface)