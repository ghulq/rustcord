use serde::{Deserialize, Deserializer};

#[inline(always)]
pub(crate) fn deserialize_default_on_error<'de, D, T>(deserializer: D) -> Result<T, D::Error>
where
    T: Default + Deserialize<'de>,
    D: Deserializer<'de>,
{
    Ok(T::deserialize(deserializer).unwrap_or_default())
}

macro_rules! py_getter_class {
    (
        $(#[$struct_meta:meta])*
        $struct_vis:vis struct $struct_name:ident {
            $(
                $(#[$struct_attr_meta:meta])*
                pub $struct_attr_name:ident: $struct_attr_ty:ty,
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
                pub $struct_attr_name: $struct_attr_ty,
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

            $($($pymethods_impl_fn_body)*)?
        }
    };
}

pub(crate) use py_getter_class;
