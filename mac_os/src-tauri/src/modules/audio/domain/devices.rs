use serde::Serialize;

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct Devices {
    pub inputs: Vec<Input>,
    pub blackhole_available: bool,
}
#[derive(Serialize)]
pub struct Input {
    pub id: String,
    pub name: String,
}
