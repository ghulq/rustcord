use serde::{Deserialize, Deserializer};

#[inline(always)]
pub(crate) fn deserialize_default_on_error<'de, D, T>(deserializer: D) -> Result<T, D::Error>
where
    T: Default + Deserialize<'de>,
    D: Deserializer<'de>,
{
    Ok(T::deserialize(deserializer).unwrap_or_default())
}
