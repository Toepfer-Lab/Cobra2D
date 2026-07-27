"""
Resources shipped with Cobra2D and the constants describing them.
"""

#: The XML namespace of the current ``schema.xsd``. Documents written by
#: :py:func:`cobra2d.Constraints.to_xml` declare it and
#: :py:func:`cobra2d.Constraints.load_from_xml` validates against it. It has to
#: be identical to the ``targetNamespace`` of ``schema.xsd``.
SCHEMA_NAMESPACE = (
    "https://github.com/Toepfer-Lab/Cobra2D/blob/main/"
    "src/cobra2d/resources/schema.xsd"
)
