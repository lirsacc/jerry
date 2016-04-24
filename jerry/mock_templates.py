import jerry.generic_template as tmpl

OPT_KEYS = ('name', 'price')


def make_options(*args, **kw):
    return [dict(zip(OPT_KEYS, opt)) for opt in [
        ("OPT_1", 120),
        ("OPT_2", 45)
    ]]


def make_option_booking(option, index):
    return tmpl.generate_generic_template([tmpl.create_element(
        title='%s (%s)' % (option['name'], option['price']),
        subtitle="Booking confirmation and link",
        buttons=[
            tmpl.create_button(
                "Download your ticket",
                url="#",
                button_type="web_url"
            ),
        ]
    )])


def make_options_offers(options):
    elements = []
    for index, item in enumerate(options):
        buttons = [
            tmpl.create_button(
                "Book option %s" % item['name'], payload='BUY::%s' % index),
            tmpl.create_button(
                "More details",
                payload='DETAILS::%s' % index),
        ]

        elements.append(tmpl.create_element(
            title='%s (%s)' % (item['name'], item['price']),
            subtitle="Some details...",
            buttons=buttons
        ))

    return tmpl.generate_generic_template(elements)


def make_option_details(option, index):
    return tmpl.generate_generic_template([tmpl.create_element(
        title='%s (%s)' % (option['name'], option['price']),
        subtitle="Moar details!!!",
        buttons=[
            tmpl.create_button(
                "Book option %s" % option['name'], payload='BUY::%s' % index),
            tmpl.create_button("See all options", payload='SEE_ALL'),
        ]
    )])
