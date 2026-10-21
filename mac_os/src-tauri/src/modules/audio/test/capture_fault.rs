use super::*;
#[test]
fn input_callback_fault_rejects_queued_audio_and_cancellation_can_stop_it() {
    let (mut sender, mut receiver) = rtrb::RingBuffer::new(2);
    sender.push([0.25; FRAME]).unwrap();
    let stop = Arc::new(AtomicBool::new(false));
    let fault = AtomicBool::new(false);
    assert!(next_frame(&mut receiver, &fault, &stop).unwrap().is_some());
    sender.push([0.25; FRAME]).unwrap();
    fault.store(true, Ordering::Release);
    assert!(matches!(
        next_frame(&mut receiver, &fault, &stop),
        Err(Error::Audio(AudioErrorCode::AudioOverrunOrDeviceLost))
    ));
    assert_eq!(receiver.slots(), 1);
    stop.store(true, Ordering::Release);
    assert!(next_frame(&mut receiver, &fault, &stop).unwrap().is_none());
}
