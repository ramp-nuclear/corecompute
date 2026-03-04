# Corecompute
This package defines the interface for asking transport questions about
a core state, and getting answers from transport codes.
The main idea is that if we define this interface in a program-agnostic
manner, we will be able to make an apples-to-apples comparison using the
same underlying model, and switching our analyses by switching the
specific implementation.

This package does not define specific Oracles for specific programs,
and those should be covered by their own packages.
