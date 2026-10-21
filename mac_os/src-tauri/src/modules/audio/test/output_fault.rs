use super::*;
#[test]
fn output_callback_fault_and_full_queue_return_distinct_typed_errors() {
    let fault = AtomicBool::new(false);
    assert!(check_fault(&fault).is_ok());
    fault.store(true, Ordering::Release);
    assert!(matches!(
        check_fault(&fault),
        Err(Error::Audio(AudioErrorCode::BlackholeOutputFailed))
    ));
    let (mut sender, mut receiver) = rtrb::RingBuffer::new(1);
    push_frame(&mut sender, [0.25; FRAME]).unwrap();
    assert!(matches!(
        push_frame(&mut sender, [0.5; FRAME]),
        Err(Error::Audio(AudioErrorCode::AudioOutputBackpressure))
    ));
    assert_eq!(receiver.pop().unwrap(), [0.25; FRAME]);
}
