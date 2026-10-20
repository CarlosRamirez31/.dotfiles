use super::AudioErrorCode;
pub type Result<T> = std::result::Result<T, Error>;

#[derive(Debug)]
pub enum Error {
    Storage,
    Audio(AudioErrorCode),
    NotFound,
    Conflict,
    Busy,
    Invalid,
    Capacity,
}
