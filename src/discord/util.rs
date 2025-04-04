use serde::{Deserialize, Deserializer};

#[inline(always)]
pub(crate) fn deserialize_default_on_error<'de, D, T>(deserializer: D) -> Result<T, D::Error>
where
    T: Default + Deserialize<'de>,
    D: Deserializer<'de>,
{
    Ok(T::deserialize(deserializer).unwrap_or_default())
}

pub(crate) trait PyRepr {
    fn repr(&self) -> String;
}

macro_rules! impl_py_repr_to_string {
    ($($type:ty),*) => {
        $(
            impl PyRepr for $type {
                #[inline(always)]
                fn repr(&self) -> String {
                    self.to_string()
                }
            }
        )*
    }
}

macro_rules! impl_py_repr_strings {
    ($($type:ty),*) => {
        $(
            impl PyRepr for $type {
                #[inline(always)]
                fn repr(&self) -> String {
                    format!("'{self}'")
                }
            }
        )*
    }
}

impl_py_repr_to_string!(u8, u16, u32, u64, u128, i8, i16, i32, i64, i128, bool);
impl_py_repr_strings!(String);

impl<T> PyRepr for Option<T>
where
    T: PyRepr,
{
    fn repr(&self) -> String {
        match self {
            Some(s) => s.repr(),
            None => String::from("None"),
        }
    }
}

macro_rules! py_repr_format_join_attrs {
    ($attr0:ident $(, $attr:ident)*) => {
        concat!(stringify!($attr0), "={}" $(, ", ", stringify!($attr), "={}")*)
    }
}

pub(crate) use py_repr_format_join_attrs;

macro_rules! py_getter_class {
    (
        $(#[$struct_meta:meta])*
        $struct_vis:vis struct $struct_name:ident {
            $(
                $(#[$struct_attr_meta:meta])*
                $struct_attr_name_vis:vis $struct_attr_name:ident: $struct_attr_ty:ty,
            )*
        }

        $(
            #[pymethods]
            impl $pymethods_struct_name:ident {
                $($pymethods_impl_fn_body:tt)*
            }
        )?
    ) => {
        $(#[$struct_meta])*
        $struct_vis struct $struct_name {
            $(
                $(#[$struct_attr_meta])*
                #[pyo3(get)]
                $struct_attr_name_vis $struct_attr_name: $struct_attr_ty,
            )*
        }

        #[pymethods]
        impl $struct_name {
            #[new]
            #[allow(clippy::too_many_arguments)]
            pub const fn new($($struct_attr_name: $struct_attr_ty,)*) -> Self {
                Self {
                    $($struct_attr_name,)*
                }
            }

            pub fn __repr__(&self) -> String {
                format!(
                    concat!(stringify!($struct_name), "(", crate::discord::util::py_repr_format_join_attrs!($($struct_attr_name),*), ")"),
                    $(crate::discord::util::PyRepr::repr(&self.$struct_attr_name)),*
                )
            }

            $($($pymethods_impl_fn_body)*)?
        }
    };
}

pub(crate) use py_getter_class;
